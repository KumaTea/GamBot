import aiohttp
from io import BytesIO
# from bot.convert import to_jpg
from common.data import STOCK_PRICE_API, UPDOWN_API, STOCK_PRICE_IMG, SINA_HEADER


async def get_raw_price(stock_code: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(STOCK_PRICE_API.format(STOCK_CODE=stock_code), headers=SINA_HEADER) as resp:
            text = await resp.text()
    raw_price = text.split('"')[1]
    return raw_price


async def get_raw_updown() -> list:
    async with aiohttp.ClientSession() as session:
        async with session.get(UPDOWN_API, headers=SINA_HEADER) as resp:
            text = await resp.text()
    raw_updown = text.split(';')
    raw_updown = [item.split('=')[-1].strip('"') for item in raw_updown if 'var' in item]
    return raw_updown


async def get_price_img(stock_code: str) -> BytesIO:
    async with aiohttp.ClientSession() as session:
        async with session.get(STOCK_PRICE_IMG.format(STOCK_CODE=stock_code), headers=SINA_HEADER) as resp:
            img_bytes = await resp.read()
    # return to_jpg(BytesIO(img_bytes))
    return BytesIO(img_bytes)
