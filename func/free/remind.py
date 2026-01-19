import asyncio
from bot.session import bot
from common.data import TEASPS_ID
from pyrogram.types import Message
from share.common import no_preview
from stock.tools import is_trading_day
from datetime import datetime, timedelta
from func.free.main import epic_free_games, steam_free_games, test_network


async def remind_free() -> Message:
    text = '今日份的免费游戏'
    inform, _ = await asyncio.gather(
        bot.send_message(TEASPS_ID, f'{text}...'),
        test_network()
    )
    steam, epic = await asyncio.gather(
        steam_free_games(),
        epic_free_games()
    )
    text += '\n\n'
    text += f'{steam}\n\n{epic}\n\n'

    tasks = ['每日签到', '低保读博']
    yesterday = datetime.now() - timedelta(hours=12)
    if is_trading_day(yesterday):
        tasks.append('查看盈亏')
    text += '另外，可以' + '、'.join(tasks) + '了'
    return await inform.edit_text(text, **no_preview)
