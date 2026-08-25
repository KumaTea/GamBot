import asyncio
import logging
from typing import Optional
from bot.session import bot
from share.common import mention_id
from telethon.tl.custom import Message
from telethon import TelegramClient as Client
from stock.main import stock_reminder
from stock.tools import is_trading_time
from func.stock.tools import query_stock, send_stock


async def remind_stock(client: Client, chat_id: int) -> Optional[Message]:
    users = stock_reminder.data.get(chat_id, {})
    if not users:
        return None
    logging.info(f'Reminding stock to {chat_id}')
    stock_summary, updown_bar, price_img = await query_stock()
    await send_stock(stock_summary, updown_bar, price_img, client, chat_id)
    remind_text = '🔊 '
    remind_text += ' '.join(mention_id(uid, name) for uid, name in users.items())
    remind_text += '\n\n还有5分钟就收盘了，记得看盘调仓！'
    remind_text += '\n\n/remind_stock 添加提醒'
    return await client.send_message(chat_id, remind_text)


async def remind_stock_all() -> None:
    if not is_trading_time():
        return None
    tasks = [remind_stock(bot, chat_id) for chat_id in stock_reminder.data]
    await asyncio.gather(*tasks)
