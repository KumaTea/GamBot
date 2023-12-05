import logging
from pyrogram import Client
from pyrogram.types import Message
from func.gacha.tools import get_image
from gacha.arknights.main import ark_data, gacha
from pyrogram.errors.exceptions.bad_request_400 import WebpageCurlFailed


async def gacha_arknights(client: Client, message: Message) -> Message:
    name, image, rarity = gacha()
    logging.info(f'func.gacha.ark\t{name=}')
    char_info = ark_data.char[name]
    char_group = char_info['group']
    char_class = char_info['class']
    char_branch = char_info['branch']

    if len(char_group) == 1:
        char_group = char_group + '国'
    limited = ''
    if '限定寻访' in char_info['approach']:
        limited = '限定'
    msg_text = f'恭喜你抽中了方舟 来自{char_group}的{rarity}星{limited}{char_class}·{char_branch}干员 **{name}**！'
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
        ark_data.save_img_id(
            name=name,
            url=image,
            img_id=img_id
        )
    return reply