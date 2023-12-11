from time import time
from pyrogram import Client
from bot.auth import ensure_not_bl
from pyrogram.types import Message
from stock.tools import is_trading_time
from stock.main import query, stock_cache


@ensure_not_bl
async def command_stock(client: Client, message: Message) -> Message:
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
    text = f'{stock_summary}\n\n{updown_bar}'
    if price_img:
        img = await message.reply_photo(price_img, quote=False)
        price_img_id = img.photo.file_id
        stock_cache.save(stock_summary, updown_bar, price_img_id)
        return await message.reply_text(text, quote=False)
    else:
        await message.reply_photo(price_img_id, quote=False)
        return await message.reply_text(text, quote=False)
