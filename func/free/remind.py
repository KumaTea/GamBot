import asyncio
from bot.session import bot
from common.data import TEASPS_ID
from pyrogram.types import Message
from func.free.main import epic_free_games, steam_free_games


async def remind_free() -> Message:
    text = '今日份的免费游戏'
    inform, steam, epic = await asyncio.gather(
        bot.send_message(TEASPS_ID, f'{text}...'),
        steam_free_games(),
        epic_free_games()
    )
    text += '\n\n'
    text += f'{steam}\n\n{epic}\n\n'
    text += '另外，可以做每日签到了'
    return await inform.edit_text(text, disable_web_page_preview=True)
