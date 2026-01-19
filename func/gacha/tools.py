import aiohttp
import logging
from io import BytesIO
from share.common import no_quote
from pyrogram.types import Message
from common.data import LOADING_DEFAULT
from pyrogram.types import InputMediaPhoto
from pyrogram.errors.exceptions.bad_request_400 import WebpageCurlFailed


async def get_image(url: str) -> BytesIO:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            img_content = await resp.read()
    img_bytes = BytesIO(img_content)
    # img_bytes.seek(0)
    img_bytes.name = 'image.png'
    return img_bytes


async def result_sender(incoming_msg: Message, text: str, image: str, loading_img: str = LOADING_DEFAULT) -> Message:
    if 'https://' in image:
        loading = await incoming_msg.reply_photo(
            photo=loading_img,
            **no_quote,
            caption=text
        )
        try:
            reply = await loading.edit_media(
                media=InputMediaPhoto(
                    media=image,
                    caption=text
                )
            )
        except WebpageCurlFailed:
            logging.error(f'Telegram server failed to get {image=}')
            img_bytes = await get_image(image)
            reply = await loading.edit_media(
                media=InputMediaPhoto(
                    media=img_bytes,
                    caption=text
                )
            )
    else:
        reply = await incoming_msg.reply_photo(
            photo=image,
            **no_quote,
            caption=text
        )
    return reply
