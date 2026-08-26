import time
import logging
from typing import Optional
from collections import deque
from urllib.parse import urlsplit
from telethon.tl.custom import Message
from telethon.tl.types import MessageEntityUrl, MessageEntityTextUrl
from bot.media import (
    MediaRef, as_ref, download_image, message_image,
    to_upload, upload_quietly, webpage_url
)
from collect.store import Item, collect_store
from collect.config import (
    Collection, PREVIEW_ACCOUNT, RECENT_MEDIA_KEEP, RECENT_MEDIA_TTL
)


class RecentMedia:
    """
    The last few pictures each chat has seen.

    A bare keyword ("ruby and me") files the picture that came just
    before it, so something has to remember what that was. Ids only --
    the message itself is re-fetched when it is actually wanted, which
    is also how we get a file reference that has not gone stale.
    """
    def __init__(self, keep: int = RECENT_MEDIA_KEEP, ttl: int = RECENT_MEDIA_TTL):
        self.keep = keep
        self.ttl = ttl
        self.chats: dict[int, deque] = {}

    def remember(self, chat_id: int, msg_id: int):
        seen = self.chats.setdefault(chat_id, deque(maxlen=self.keep))
        seen.append((msg_id, time.time()))

    def latest(self, chat_id: int) -> Optional[int]:
        seen = self.chats.get(chat_id)
        if not seen:
            return None
        now = time.time()
        while seen:
            msg_id, when = seen[-1]
            if now - when <= self.ttl:
                return msg_id
            seen.pop()
        return None

    def forget(self, chat_id: int, msg_id: int):
        seen = self.chats.get(chat_id)
        if seen:
            self.chats[chat_id] = deque(
                (i for i in seen if i[0] != msg_id), maxlen=self.keep)


recent_media = RecentMedia()


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
    url = webpage_url(message)

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
        return f'{collection.label} +1（共 {collect_store.count(collection.name)} 张）'

    # A link Telegram has not unfurled -- go and get it ourselves.
    link = url or first_link(message)
    if link:
        return await archive_url(collection, link, message.client, added_by)
    return None


IMAGE_SUFFIXES = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp')


def looks_like_image_url(url: str) -> bool:
    """
    Whether a link points straight at a picture.

    A page link (an X post, say) is not one: a bot cannot make Telegram
    render a preview, so there is nothing behind it we could ever get.
    """
    if not url:
        return False
    return urlsplit(url).path.lower().endswith(IMAGE_SUFFIXES)


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
        return f'{collection.label}：这个链接已经存过了。'

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
        return f'{collection.label}：这张已经存过了。'
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
    stuck = f'{collection.label}：这个链接里没有能直接取到的图片，把图转发过来吧。'
    if not PREVIEW_ACCOUNT:
        return stuck

    try:
        await client.send_message(PREVIEW_ACCOUNT, url)
    except Exception as e:
        logging.warning(f'[collect]\tCould not reach the preview account: {e}')
        return stuck
    return f'{collection.label}：链接交给取图的账号了，取到就存。'


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
