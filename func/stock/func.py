from pyrogram import Client
from bot.auth import ensure_not_bl
from pyrogram.types import Message
from stock.main import stock_reminder
from func.stock.tools import query_stock, send_and_cache


@ensure_not_bl
async def command_stock(client: Client, message: Message) -> Message:
    stock_summary, updown_bar, price_img, price_img_id = await query_stock()
    return await send_and_cache(stock_summary, updown_bar, price_img, price_img_id, message=message)


@ensure_not_bl
async def command_remind_stock(client: Client, message: Message) -> Message:
    chat_id = message.chat.id
    user = message.from_user
    result = stock_reminder.add(chat_id, user)
    if result:
        text = '投资提醒已设定'
    else:
        text = '您已经设定了投资提醒'
    text += '\n\n可使用 /forget_stock 取消投资提醒'
    return await message.reply_text(text, quote=False)


@ensure_not_bl
async def command_forget_stock(client: Client, message: Message) -> Message:
    chat_id = message.chat.id
    user = message.from_user
    result = stock_reminder.remove(chat_id, user)
    if result:
        text = '投资提醒已取消'
    else:
        text = '您尚未设定投资提醒'
    text += '\n\n可使用 /remind_stock 设定投资提醒'
    return await message.reply_text(text, quote=False)
