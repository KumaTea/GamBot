import logging
from telethon.tl.custom import Message
from func.gacha.tools import result_sender
from gacha.genshin.main import gacha


async def gacha_genshin(event) -> Message:
    name, image, _, type_str = gacha()
    logging.info(f'[gacha]\tgenshin {name=}')
    return await result_sender(event, f'恭喜你抽中了原神 {type_str} **{name}**！', image)
