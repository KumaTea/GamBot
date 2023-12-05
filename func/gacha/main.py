from pyrogram import Client
from bot.auth import ensure_not_bl
from pyrogram.types import Message
from func.gacha.genshin import gacha_genshin
from func.gacha.arknights import gacha_arknights
from common.data import *
from bot.tools import get_command_content


pools = {
    'genshin': GACHA_GENSHIN_CMD,
    'arknights': GACHA_ARKNIGHTS_CMD,
}


@ensure_not_bl
async def command_gacha(client: Client, message: Message) -> Message:
    content = get_command_content(message)
    if not content:
        return await message.reply_text('你没有指定池子！', quote=False)

    match = ''
    content = content.lower()
    for pool in pools:
        if content in pools[pool]:
            match = pool
    if match == 'genshin':
        return await gacha_genshin(client, message)
    elif match == 'arknights':
        return await gacha_arknights(client, message)

    return await message.reply_text('找不到指定的池子！', quote=False)
