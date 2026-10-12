import asyncio
import logging
from typing import Optional
from collections import OrderedDict
from telethon.tl.custom import Message
from telethon.tl.types import MessageEntityUrl, MessageEntityTextUrl
from bot.media import (
    MediaRef, as_ref, download_image, message_image,
    to_upload, upload_quietly, webpage_url
)
from collect.store import Item, collect_store
from collect.config import Collection, PREVIEW_ACCOUNT


# -- what a report is


class Fleeting(str):
    """
    A report worth saying now and not worth keeping.

    An ordinary string wherever it is joined, formatted or sent -- the
    type is only there so that whoever sends it knows to take it back
    afterwards.
    """


FLEETING_TTL = 5 * 60   # a report that answers "did that go anywhere?"

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


def filed(collection: Collection, item_id: int) -> str:
    """
    The line that says a picture went in.

    It names the row, so `/ruby delete <id>` can take it straight back
    out -- the running total next to it is not an id, since deleted rows
    leave gaps behind them.
    """
    return f'{collection.label} +1（#{item_id}，共 {collect_store.count(collection.name)} 张）'


# -- filing


async def archive_message(
        collection: Collection,
        message: Message,
        added_by: int = None,
        asked_by: Message = None
) -> Optional[str]:
    """
    File the picture a message carries.

    Returns a line to report back, or None if there was no picture in
    it at all -- which is not an error, just nothing to do. `asked_by`
    is the message that asked, and is where a picture fetched from a
    link gets shown once it arrives.
    """
    picture = message_image(message)
    # where it came from, as far as the message says: the preview's own
    # url, or failing that a link in the caption
    url = webpage_url(message) or first_link(message)

    if picture is not None:
        ref = as_ref(picture)
        if ref and collect_store.has_media(collection.name, ref.id):
            return f'{collection.label}：这张已经存过了。'
        item_id = collect_store.add(
            collection.name,
            ref=ref,
            src_chat_id=message.chat_id,
            src_msg_id=message.id,
            url=url,
            added_by=added_by,
        )
        if item_id is None:
            return f'{collection.label}：这张已经存过了。'
        return filed(collection, item_id)

    # A link Telegram has not unfurled -- go and get it ourselves.
    if url:
        return await archive_url(collection, url, message.client, added_by, asked_by)
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
        added_by: int = None,
        asked_by: Message = None
) -> str:
    """
    File a picture that is not on Telegram yet.

    We fetch it, hand it to Telegram without sending it to anybody, and
    keep both the resulting media and the bytes -- the media so the next
    `/ruby` is a single call, the bytes so it can be rebuilt when that
    media expires.
    """
    if collect_store.by_url(collection.name, url):
        return f'{collection.label}：这个链接已经存过了。'

    content = await download_image(url)
    if not content:
        # Either the host refused us, or -- far more often -- the link is
        # a page rather than a picture. A bot cannot ask Telegram what is
        # on a page (`messages.getWebPagePreview` is BOT_METHOD_INVALID),
        # so somebody who can has to go and look.
        return await hand_to_preview(collection, url, client, asked_by)

    ref = await upload_quietly(client, content)
    item_id = collect_store.add(
        collection.name,
        ref=ref,
        blob=content,
        url=url,
        added_by=added_by,
    )
    if item_id is None:
        return f'{collection.label}：这张已经存过了。'
    return filed(collection, item_id)


# The link the bot handed the preview account -> the message that asked
# for it, as (chat id, message id). The account's picture comes back as
# a reply to the link, which is how it finds its way home. Kept in
# memory only: a restart in between costs the picture being shown, not
# it being filed.
waiting: OrderedDict[int, tuple[int, int]] = OrderedDict()
WAITING_KEEP = 100


async def hand_to_preview(
        collection: Collection,
        url: str,
        client,
        asked_by: Message = None
) -> str:
    """
    Ask the preview account what the picture behind a page link is.

    Nothing is waited for. The account answers with a picture of its
    own accord -- a second or two later, once Telegram has fetched the
    page -- and that arrives as an ordinary message, which files itself
    when it does. So there is no request to hold open and nothing to
    time out; all that is remembered is where to show the result.
    """
    stuck = f'{collection.label}：这个链接里没有能直接取到的图片，把图转发过来吧。'
    if not PREVIEW_ACCOUNT:
        return stuck

    try:
        sent = await client.send_message(PREVIEW_ACCOUNT, url)
    except Exception as e:
        logging.warning(f'[collect]\tCould not reach the preview account: {e}')
        return stuck

    if asked_by is not None:
        waiting[sent.id] = (asked_by.chat_id, asked_by.id)
        while len(waiting) > WAITING_KEEP:
            waiting.popitem(last=False)

    # said now and gone in five minutes: the picture it promises turns
    # up under the request, with its id, once it is filed -- so this
    # line is only ever an answer to "did that go anywhere?"
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
