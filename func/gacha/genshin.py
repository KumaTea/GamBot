import logging
from pyrogram import Client
from pyrogram.types import Message
from common.data import LOADING_GENSHIN
from gacha.genshin.main import ys_data, gacha
from func.gacha.tools import result_sender


async def gacha_genshin(client: Client, message: Message) -> Message:
    name, image, gacha_type, type_str = gacha()
    logging.info(f'func.gacha.gs\t{name=}')
    msg_text = f'恭喜你抽中了原神 {type_str} **{name}**！'
    reply = await result_sender(
        incoming_msg=message,
        text=msg_text,
        image=image,
        loading_img=LOADING_GENSHIN
    )
    if 'http' in image:
        img_id = reply.photo.file_id
        ys_data.save_img_id(
            data_type=gacha_type,
            name=name,
            img_id=img_id
        )
    return reply
