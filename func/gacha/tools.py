import logging
from typing import Optional
from telethon.tl.custom import Message
from bot.media import as_ref, download_image, to_upload
from bot.media_cache import media_cache


NO_IMAGE = '\n\n(图片暂缺)'


async def result_sender(event, text: str, image: str) -> Optional[Message]:
    """
    Send a gacha result, however the picture can be got hold of.

    First choice is media Telegram already holds; then the url, which
    Telegram fetches itself; and last the bytes, for the wikis that turn
    Telegram's fetcher away but not ours. Whatever works is remembered.
    """
    if not image:
        return await event.respond(text + NO_IMAGE)

    cached = media_cache.get(image)
    if cached:
        try:
            return await event.respond(text, file=cached.to_input())
        except Exception as e:
            logging.info(f'[gacha]\tCached media for {image} no longer works: {e}')
            media_cache.drop(image)

    try:
        sent = await event.respond(text, file=image)
    except Exception as e:
        logging.warning(f'[gacha]\tTelegram could not fetch {image}: {e}')
        sent = await upload_ourselves(event, text, image)

    if sent:
        remember(image, sent)
    return sent


async def upload_ourselves(event, text: str, image: str) -> Optional[Message]:
    content = await download_image(image)
    if not content:
        return await event.respond(text + NO_IMAGE)
    try:
        return await event.respond(text, file=to_upload(content))
    except Exception as e:
        logging.error(f'[gacha]\tCould not send {image} at all: {e}')
        return await event.respond(text + NO_IMAGE)


def remember(url: str, sent: Message):
    ref = as_ref(sent.media)
    if ref:
        media_cache.put(url, ref)
