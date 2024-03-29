import random
import asyncio
from pyrogram import Client
from share.auth import ensure_auth
from pyrogram.types import Message
from common.info import administrators
from bot.tools import get_command_content
from func.gacha.genshin import gacha_genshin
from func.gacha.arknights import gacha_arknights
from func.gacha.groupmem import run_pic_bot, gacha_group_member
from common.data import GACHA_GENSHIN_CMD, GACHA_GROUPMEM_CMD, GACHA_ARKNIGHTS_CMD


pools = {
    'genshin': GACHA_GENSHIN_CMD,
    'arknights': GACHA_ARKNIGHTS_CMD,
    'groupmem': GACHA_GROUPMEM_CMD
}


@ensure_auth
async def command_gacha(client: Client, message: Message) -> Message:
    content = get_command_content(message)
    if not content:
        # return await message.reply_text('你没有指定池子！', quote=False)
        match = random.choice(list(pools.keys()))
    else:
        match = None
        content = content.lower()
        for pool in pools:
            if content in pools[pool]:
                match = pool
    if match == 'genshin':
        return await gacha_genshin(client, message)
    elif match == 'arknights':
        return await gacha_arknights(client, message)
    elif match == 'groupmem':
        return await gacha_group_member(client, message)

    return await message.reply_text('找不到指定的池子！', quote=False)


@ensure_auth
async def command_gacha_genshin(client: Client, message: Message) -> Message:
    return await gacha_genshin(client, message)


@ensure_auth
async def command_gacha_arknights(client: Client, message: Message) -> Message:
    return await gacha_arknights(client, message)


@ensure_auth
async def command_gacha_groupmem(client: Client, message: Message) -> Message:
    return await gacha_group_member(client, message)


# no need to ensure_auth
async def force_refresh(client: Client, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    if user_id not in administrators:
        return None
    await asyncio.gather(
        run_pic_bot(chat_id, forced=True),
        message.reply_text(f'已强制刷新群 {chat_id} 的头像！', quote=False)
    )
