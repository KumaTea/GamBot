import logging
import asyncio
from pyrogram import Client
from typing import Optional
from bot.session import bot
from pyrogram.types import Message
from stock.main import stock_reminder
from stock.tools import is_trading_time
from func.stock.tools import query_stock, send_and_cache


async def remind_stock(client: Client, chat_id: int) -> Optional[Message]:
    users = stock_reminder.data.get(chat_id, [])
    if not users:
        return None
    logging.info(f'Reminding stock to {chat_id}')
    stock_summary, updown_bar, price_img, price_img_id = await query_stock()
    await send_and_cache(stock_summary, updown_bar, price_img, price_img_id, client, chat_id)
    remind_text = ' '.join(user.mention() for user in users)
    remind_text += '\n\n还有5分钟就收盘了，记得看盘调仓！'
    return await client.send_message(chat_id, remind_text)


async def remind_stock_all() -> None:
    trading = is_trading_time()
    if not trading:
        return None
    tasks = []
    for chat_id in stock_reminder.data.keys():
        tasks.append(remind_stock(bot, chat_id))
    await asyncio.gather(*tasks)
