import logging
from telethon.tl.custom import Message
from func.gacha.tools import result_sender
from gacha.arknights.main import gacha, ark_data


async def gacha_arknights(event) -> Message:
    name, image, rarity = gacha()
    logging.info(f'[gacha]\tarknights {name=}')

    info = ark_data.char[name]
    group = info['group']
    if len(group) == 1:
        group += '国'
    limited = '限定' if any('限定' in a for a in info.get('approach') or ()) else ''

    text = (f'恭喜你抽中了方舟 来自{group}的{rarity}星{limited}'
            f'{info["class"]}·{info["branch"]}干员 **{name}**！')
    return await result_sender(event, text, image)
