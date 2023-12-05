from time import time
from pyrogram import Client
from stock.main import query
from bot.auth import ensure_not_bl
from pyrogram.types import Message
from stock.tools import save_cache, is_trading_time


class LastSave:
    def __init__(self):
        self.stock_summary = ''
        self.updown_bar = ''
        self.price_img_id = ''
        self.last_timestamp = 0


last_save = LastSave()


@ensure_not_bl
async def command_stock(client: Client, message: Message) -> Message:
    now_timestamp = int(time())
    trading = is_trading_time()
    no_cache = False
    if trading and now_timestamp - last_save.last_timestamp > 30:
        no_cache = True
    stock_summary, updown_bar, price_img, price_img_id = await query(trading, no_cache)
    text = f'{stock_summary}\n\n{updown_bar}'
    if price_img:
        img = await message.reply_photo(price_img, quote=False)
        price_img_id = img.photo.file_id
        if not trading:
            save_cache(stock_summary, updown_bar, price_img_id)
        return await message.reply_text(text, quote=False)
    else:
        await message.reply_photo(price_img_id, quote=False)
        return await message.reply_text(text, quote=False)
