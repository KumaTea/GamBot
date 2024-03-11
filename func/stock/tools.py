from time import time
from io import BytesIO
from pyrogram import Client
from typing import Tuple, Optional
from pyrogram.types import Message
from stock.tools import is_trading_time
from stock.main import query, stock_cache


async def query_stock() -> Tuple[str, str, Optional[BytesIO], Optional[str]]:
    now_timestamp = int(time())
    trading = is_trading_time()
    no_cache = False
    if trading and now_timestamp - stock_cache.last_timestamp > 30:
        no_cache = True
    elif now_timestamp - stock_cache.last_timestamp > 2 * 60 * 60:  # 2 hours
        no_cache = True
    elif trading != stock_cache.trading:
        no_cache = True
    stock_summary, updown_bar, price_img, price_img_id = await query(trading, no_cache)
    return stock_summary, updown_bar, price_img, price_img_id


async def send_and_cache(
        stock_summary: str,
        updown_bar: str,
        price_img: BytesIO = None,
        price_img_id: str = None,
        client: Client = None,
        chat_id: int = None,
        message: Message = None
) -> Message:
    assert (client and chat_id) or message
    text = f'{stock_summary}\n{updown_bar}'
    if message:
        if price_img:
            img = await message.reply_photo(price_img, quote=False)
            price_img_id = img.photo.file_id
            stock_cache.save(stock_summary, updown_bar, price_img_id)
            return await message.reply_text(text, disable_web_page_preview=True, quote=False)
        else:
            await message.reply_photo(price_img_id, quote=False)
            return await message.reply_text(text, disable_web_page_preview=True, quote=False)
    else:
        if price_img:
            img = await client.send_photo(chat_id, photo=price_img)
            price_img_id = img.photo.file_id
            stock_cache.save(stock_summary, updown_bar, price_img_id)
            return await client.send_message(chat_id, text, disable_web_page_preview=True)
        else:
            await client.send_photo(chat_id, photo=price_img_id)
            return await client.send_message(chat_id, text, disable_web_page_preview=True)
