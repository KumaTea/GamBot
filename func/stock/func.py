from typing import Optional
from share.auth import ensure_auth
from telethon.tl.custom import Message
from share.common import get_command_args
from stock.main import query_symbol, stock_reminder
from stock.quote import quote_link
from stock.format import format_quote, missing
from func.stock.tools import query_stock, send_stock


@ensure_auth
async def command_stock(event) -> Optional[Message]:
    """`/stock` for the indices, `/stock 600519` for one symbol."""
    args = get_command_args(event.raw_text)
    if not args:
        stock_summary, updown_bar, price_img = await query_stock()
        return await send_stock(stock_summary, updown_bar, price_img, event=event)

    wanted = args[0]
    code, quote, chart = await query_symbol(wanted)
    if not quote:
        return await event.respond(missing(wanted))

    text = format_quote(quote, quote_link(code))
    return await send_stock(text, '', chart, event=event)


@ensure_auth
async def command_remind_stock(event) -> Message:
    user = await event.get_sender()
    result = stock_reminder.add(event.chat_id, user)
    text = '投资提醒已设定' if result else '您已经设定了投资提醒'
    text += '\n\n可使用 /forget_stock 取消投资提醒'
    return await event.respond(text)


@ensure_auth
async def command_forget_stock(event) -> Message:
    user = await event.get_sender()
    result = stock_reminder.remove(event.chat_id, user)
    text = '投资提醒已取消' if result else '您尚未设定投资提醒'
    text += '\n\n可使用 /remind_stock 设定投资提醒'
    return await event.respond(text)
