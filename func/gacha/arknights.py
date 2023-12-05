import logging
from pyrogram import Client
from pyrogram.types import Message
from common.data import LOADING_ARKNIGHTS
from func.gacha.tools import result_sender
from gacha.arknights.main import ark_data, gacha


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
    reply = await result_sender(
        incoming_msg=message,
        text=msg_text,
        image=image,
        loading_img=LOADING_ARKNIGHTS
    )
    if 'http' in image:
        img_id = reply.photo.file_id
        ark_data.save_img_id(
            name=name,
            url=image,
            img_id=img_id
        )
    return reply
