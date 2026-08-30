import time
import asyncio
import logging
from typing import Optional
from collections import deque
from telethon.tl.custom import Message
from telethon.tl.types import MessageEntityUrl, MessageEntityTextUrl
from bot.media import (
    MediaRef, as_ref, download_image, message_image,
    to_upload, upload_quietly, webpage_url
)
from collect.store import Item, collect_store
from collect.config import (
    Collection, PREVIEW_ACCOUNT, RECENT_KEEP, RECENT_TTL
)


# -- what a report is


class Quiet(str):
    """
    A report to make only when it was asked for.

    A keyword is a word before it is an instruction -- "ruby" turns up
    in ordinary sentences, and one of those that happens to follow a
    link should not be answered with a complaint about the link. Aimed
    deliberately at something, by `/ruby` or in the bot's own chat, the
    same words answer a question somebody asked, and get said.
    """


class Fleeting(str):
    """
    A report worth saying now and not worth keeping.

    An ordinary string wherever it is joined, formatted or sent -- the
    type is only there so that whoever sends it knows to take it back
    afterwards.
    """


FLEETING_TTL = 5 * 60   # a report that answers "did that go anywhere?"
BRIEF_TTL = 5           # a report nobody needs to read twice

_fading = set()


def fade(message: Message, after: int = FLEETING_TTL):
    """
    Take a message back once it has stopped being news.

    The task is held onto for as long as it runs: asyncio keeps only a
    weak reference to one, and a collected task would leave the message
    sitting there forever. A restart in the meantime does the same, and
    is not worth a scheduler to avoid -- the message is clutter then,
    not a lie.
    """
    async def wait():
        await asyncio.sleep(after)
        try:
            await message.delete()
        except Exception as e:
            logging.warning(f'[collect]\tCould not take back {message.id}: {e}')

    task = asyncio.create_task(wait())
    _fading.add(task)
    task.add_done_callback(_fading.discard)


# -- what a keyword can point back at


class RecentMessages:
    """
    The last few messages each person sent in each chat.

    A bare keyword ("ruby and me") files the picture that came just
    before it, so something has to remember what that was. The messages
    are kept whole rather than by id: reaching one then costs nothing,
    where re-fetching it would be a round trip to ask Telegram for
    something we were handed already.

    Keeping them per person is what makes another bot talking in between
    harmless -- it takes none of the lookback up, because it is not in
    the same queue. Only whoever may file gets remembered; nobody else's
    message can be what a keyword points at.
    """
    def __init__(self, keep: int = RECENT_KEEP, ttl: int = RECENT_TTL):
        self.keep = keep
        self.ttl = ttl
        self.seen: dict[tuple[int, int], deque] = {}

    def remember(self, chat_id: int, sender_id: int, message: Message):
        recent = self.seen.setdefault((chat_id, sender_id), deque(maxlen=self.keep))
        recent.append((message, time.time()))

    def before(self, chat_id: int, sender_id: int) -> Optional[Message]:
        """
        The last thing this person said that there would be any point
        filing -- newest first, and nothing older than the ttl.
        """
        recent = self.seen.get((chat_id, sender_id))
        if not recent:
            return None

        now = time.time()
        for message, when in reversed(recent):
            if now - when > self.ttl:
                break  # everything further back is older still
            if carries_picture(message):
                return message
        return None

    def clear(self, chat_id: int, sender_id: int):
        """Forget the lot, so the next keyword has nothing to point at."""
        self.seen.pop((chat_id, sender_id), None)

    def forget(self, chat_id: int, sender_id: int, msg_id: int):
        recent = self.seen.get((chat_id, sender_id))
        if recent:
            self.seen[(chat_id, sender_id)] = deque(
                (i for i in recent if i[0].id != msg_id), maxlen=self.keep)


recent_messages = RecentMessages()


# -- filing


async def archive_message(
        collection: Collection,
        message: Message,
        added_by: int = None
) -> Optional[str]:
    """
    File the picture a message carries.

    Returns a line to report back, or None if there was no picture in
    it at all -- which is not an error, just nothing to do.
    """
    picture = message_image(message)
    # where it came from, as far as the message says: the preview's own
    # url, or failing that a link in the caption
    url = webpage_url(message) or first_link(message)

    if picture is not None:
        ref = as_ref(picture)
        if ref and collect_store.has_media(collection.name, ref.id):
            return Quiet(f'{collection.label}：这张已经存过了。')
        item_id = collect_store.add(
            collection.name,
            ref=ref,
            src_chat_id=message.chat_id,
            src_msg_id=message.id,
            url=url,
            added_by=added_by,
        )
        if item_id is None:
            return Quiet(f'{collection.label}：这张已经存过了。')
        return f'{collection.label} +1（共 {collect_store.count(collection.name)} 张）'

    # A link Telegram has not unfurled -- go and get it ourselves.
    if url:
        return await archive_url(collection, url, message.client, added_by)
    return None


def carries_picture(message: Message) -> bool:
    """
    Whether there is anything in a message worth trying to file.

    A link counts, and not only one that points straight at an image
    file: what is behind a page link can be reached now too, by way of
    the preview account.
    """
    return message_image(message) is not None or bool(
        webpage_url(message) or first_link(message))


def first_link(message: Message) -> Optional[str]:
    """The first url in a message, from Telegram's own entity parsing."""
    for entity, text in (message.get_entities_text() or ()):
        if not isinstance(entity, (MessageEntityUrl, MessageEntityTextUrl)):
            continue
        url = getattr(entity, 'url', None) or text
        if url and url.startswith(('http://', 'https://')):
            return url
    return None


async def archive_url(
        collection: Collection,
        url: str,
        client,
        added_by: int = None
) -> str:
    """
    File a picture that is not on Telegram yet.

    We fetch it, hand it to Telegram without sending it to anybody, and
    keep both the resulting media and the bytes -- the media so the next
    `/ruby` is a single call, the bytes so it can be rebuilt when that
    media expires.
    """
    if collect_store.by_url(collection.name, url):
        return Quiet(f'{collection.label}：这个链接已经存过了。')

    content = await download_image(url)
    if not content:
        # Either the host refused us, or -- far more often -- the link is
        # a page rather than a picture. A bot cannot ask Telegram what is
        # on a page (`messages.getWebPagePreview` is BOT_METHOD_INVALID),
        # so somebody who can has to go and look.
        return await hand_to_preview(collection, url, client)

    ref = await upload_quietly(client, content)
    item_id = collect_store.add(
        collection.name,
        ref=ref,
        blob=content,
        url=url,
        added_by=added_by,
    )
    if item_id is None:
        return Quiet(f'{collection.label}：这张已经存过了。')
    return f'{collection.label} +1（共 {collect_store.count(collection.name)} 张）'


async def hand_to_preview(collection: Collection, url: str, client) -> str:
    """
    Ask the preview account what the picture behind a page link is.

    Nothing is waited for. The account answers with a picture of its
    own accord -- a second or two later, once Telegram has fetched the
    page -- and that arrives as an ordinary message, which files itself
    when it does. So there is no request to hold open, nothing to time
    out, and nothing to remember in between.
    """
    stuck = Quiet(
        f'{collection.label}：这个链接里没有能直接取到的图片，把图转发过来吧。')
    if not PREVIEW_ACCOUNT:
        return stuck

    try:
        await client.send_message(PREVIEW_ACCOUNT, url)
    except Exception as e:
        logging.warning(f'[collect]\tCould not reach the preview account: {e}')
        return stuck
    # said now and gone in five minutes: the picture it promises files
    # itself and reports where it lands, so this line is only ever an
    # answer to "did that go anywhere?"
    return Fleeting(f'{collection.label}：链接交给取图的账号了，取到就存。')


# -- handing back out


async def sendable(client, item: Item):
    """
    Something `send_file` will accept for this item, cheapest first.

    The stored media reference is tried first and is usually enough.
    When Telegram has expired it we go back to whatever the picture came
    from -- the original message, the saved bytes, the url -- and put a
    fresh reference in its place.
    """
    ref = item.ref
    if ref:
        yield ref.to_input(), None

    if item.src_chat_id and item.src_msg_id:
        message = await refetch(client, item.src_chat_id, item.src_msg_id)
        picture = message_image(message)
        if picture is not None:
            yield picture, as_ref(picture)

    if item.blob_path:
        try:
            with open(item.blob_path, 'rb') as f:
                content = f.read()
        except OSError as e:
            logging.warning(f'[collect]\tCannot read {item.blob_path}: {e}')
        else:
            yield to_upload(content), None

    if item.url:
        content = await download_image(item.url)
        if content:
            if not item.blob_path:
                collect_store.save_blob(item.id, content)
            yield to_upload(content), None


async def refetch(client, chat_id: int, msg_id: int) -> Optional[Message]:
    try:
        return await client.get_messages(chat_id, ids=msg_id)
    except Exception as e:
        logging.warning(f'[collect]\tCannot re-read {chat_id}/{msg_id}: {e}')
        return None


async def send_item(event, item: Item, caption: str = None) -> Optional[Message]:
    """Send one stored picture, refreshing what has gone stale on the way."""
    client = event.client
    stale = False

    async for media, fresh_ref in sendable(client, item):
        try:
            sent = await event.respond(caption or '', file=media)
        except Exception as e:
            logging.warning(f'[collect]\tCould not send item {item.id}: {e}')
            stale = True
            continue

        remember_ref(item, fresh_ref or as_ref(sent.media), stale)
        return sent

    logging.error(f'[collect]\tItem {item.id} is unreachable by every route')
    return None


def remember_ref(item: Item, ref: Optional[MediaRef], stale: bool):
    """Keep the reference that just worked, so the next send is one call."""
    if not ref:
        if stale:
            collect_store.clear_ref(item.id)
        return
    if stale or item.media_id != ref.id or item.file_ref != ref.file_reference:
        collect_store.update_ref(item.id, ref)
