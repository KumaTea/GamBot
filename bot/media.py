import logging
import aiohttp
from io import BytesIO
from typing import Optional, Union
from dataclasses import dataclass
from telethon import utils
from telethon.tl import functions, types
from telethon.tl.custom import Message
from share.data import USER_AGENT


# Telegram's own fetcher is blocked by a fair number of image hosts.
# When we download a picture ourselves, look like a browser instead.
IMAGE_HEADERS = {'User-Agent': USER_AGENT}
DOWNLOAD_TIMEOUT = 30
MAX_IMAGE_BYTES = 20 * 1024 * 1024  # Telegram's own limit for bot uploads
CHUNK_SIZE = 64 * 1024

PHOTO = 'photo'
DOCUMENT = 'document'


@dataclass(slots=True)
class MediaRef:
    """
    Enough to re-send a picture that already lives on Telegram.

    Telethon cannot use a Bot API `file_id`, but an `InputPhoto` built
    from these three numbers is the same idea and works everywhere.
    `file_reference` is the part that goes stale -- Telegram expires it
    after a while -- so a ref is a *cache*, never the only copy: whoever
    stores one has to keep a way of getting a fresh one.
    """
    kind: str
    id: int
    access_hash: int
    file_reference: bytes

    def to_input(self) -> Union[types.InputPhoto, types.InputDocument]:
        if self.kind == PHOTO:
            return types.InputPhoto(self.id, self.access_hash, self.file_reference)
        return types.InputDocument(self.id, self.access_hash, self.file_reference)


def as_ref(media) -> Optional[MediaRef]:
    """A `MediaRef` for any photo/document-ish object, or None."""
    if isinstance(media, types.MessageMediaPhoto):
        media = media.photo
    elif isinstance(media, types.MessageMediaDocument):
        media = media.document

    if isinstance(media, types.Photo):
        return MediaRef(PHOTO, media.id, media.access_hash, media.file_reference)
    if isinstance(media, types.Document):
        return MediaRef(DOCUMENT, media.id, media.access_hash, media.file_reference)
    return None


def is_image_document(document: types.Document) -> bool:
    mime = (document.mime_type or '').lower()
    if mime.startswith('image/'):
        return True
    return any(
        isinstance(a, (types.DocumentAttributeImageSize, types.DocumentAttributeAnimated))
        for a in (document.attributes or ())
    )


def message_image(message: Message):
    """
    The picture a message carries, wherever it is hiding.

    A link that Telegram has already unfurled keeps a full-size photo on
    the webpage preview -- not a thumbnail -- and that photo can be
    re-sent like any other, so it counts.
    """
    if not message:
        return None

    media = message.media
    if isinstance(media, types.MessageMediaPhoto):
        return media.photo
    if isinstance(media, types.MessageMediaDocument):
        document = media.document
        if isinstance(document, types.Document) and is_image_document(document):
            return document
        return None
    if isinstance(media, types.MessageMediaWebPage):
        page = media.webpage
        photo = getattr(page, 'photo', None)
        if isinstance(photo, types.Photo):
            return photo
        document = getattr(page, 'document', None)
        if isinstance(document, types.Document) and is_image_document(document):
            return document
    return None


def webpage_url(message: Message) -> Optional[str]:
    """The url of a link preview, if the message has one."""
    media = getattr(message, 'media', None)
    if isinstance(media, types.MessageMediaWebPage):
        return getattr(media.webpage, 'url', None)
    return None


async def download_image(url: str) -> Optional[bytes]:
    """
    Fetch a picture ourselves.

    Returns None rather than raising: a picture we cannot get is a thing
    to log and move past, not a reason to take the handler down.
    """
    timeout = aiohttp.ClientTimeout(total=DOWNLOAD_TIMEOUT)
    try:
        async with aiohttp.ClientSession(timeout=timeout, headers=IMAGE_HEADERS) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    logging.warning(f'[media]\t{url} returned HTTP {resp.status}')
                    return None
                kind = (resp.headers.get('Content-Type') or '').lower()
                # `read(n)` returns whatever has arrived, not n bytes, so
                # a single call quietly truncates anything over one chunk
                chunks = []
                size = 0
                async for chunk in resp.content.iter_chunked(CHUNK_SIZE):
                    chunks.append(chunk)
                    size += len(chunk)
                    if size > MAX_IMAGE_BYTES:
                        logging.warning(f'[media]\t{url} is larger than {MAX_IMAGE_BYTES} bytes')
                        return None
                content = b''.join(chunks)
    except Exception as e:
        logging.warning(f'[media]\tCould not download {url}: {e}')
        return None

    if not content:
        logging.warning(f'[media]\t{url} is empty')
        return None
    # a link is not a picture just because someone sent it -- without
    # this an article url would be filed as one. Some hosts label their
    # images `application/octet-stream`, so the bytes get the last word.
    if not (kind.startswith('image/') or looks_like_image(content)):
        logging.info(f'[media]\t{url} is {kind or "of unknown type"}, not a picture')
        return None
    return content


IMAGE_MAGIC = (
    b'\xff\xd8\xff',      # jpeg
    b'\x89PNG\r\n\x1a\n',  # png
    b'GIF87a', b'GIF89a',  # gif
    b'BM',                 # bmp
)


def looks_like_image(content: bytes) -> bool:
    if content.startswith(IMAGE_MAGIC):
        return True
    # riff containers say what they hold four bytes in
    return content[:4] == b'RIFF' and content[8:12] == b'WEBP'


def to_upload(content: bytes, name: str = 'image.jpg') -> BytesIO:
    stream = BytesIO(content)
    stream.name = name
    return stream


async def upload_quietly(client, file, name: str = 'image.jpg') -> Optional[MediaRef]:
    """
    Put a picture on Telegram's servers *without sending it anywhere*.

    `messages.uploadMedia` against ourselves hands back real, reusable
    media -- the same thing a `file_id` names -- and nobody receives a
    message for it.
    """
    if isinstance(file, bytes):
        file = to_upload(file, name)
    try:
        handle = await client.upload_file(file)
        media = await client(functions.messages.UploadMediaRequest(
            peer=types.InputPeerSelf(),
            media=types.InputMediaUploadedPhoto(handle)
        ))
    except Exception as e:
        logging.warning(f'[media]\tCould not pre-upload {name}: {e}')
        return None
    return as_ref(media)


def pack_file_id(media) -> Optional[str]:
    """
    The Bot API `file_id` for some media, for human consumption.

    Telethon cannot send one of these back, so it is only ever shown,
    never stored as the way back to a picture.
    """
    try:
        return utils.pack_bot_file_id(media)
    except Exception:
        return None
