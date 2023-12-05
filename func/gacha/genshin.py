import logging
from pyrogram import Client
from pyrogram.types import Message
from func.gacha.tools import get_image
from gacha.genshin.main import ys_data, gacha
from pyrogram.errors.exceptions.bad_request_400 import WebpageCurlFailed


async def gacha_genshin(client: Client, message: Message) -> Message:
    name, image, gacha_type, type_str = gacha()
    logging.info(f'func.gacha.gs\t{name=}')
    msg_text = f'恭喜你抽中了原神 {type_str} **{name}**！'
    try:
        reply = await message.reply_photo(
            photo=image,
            quote=False,
            caption=msg_text
        )
    except WebpageCurlFailed:
        logging.error(f'Telegram server failed to get {image=}')
        img_bytes = await get_image(image)
        reply = await message.reply_photo(
            photo=img_bytes,
            quote=False,
            caption=msg_text
        )
    if 'http' in image:
        img_id = reply.photo.file_id
        ys_data.save_img_id(
            data_type=gacha_type,
            name=name,
            img_id=img_id
        )
    return reply
