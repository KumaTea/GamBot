import aiohttp
from PIL import Image
from io import BytesIO
from common.data import *


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
    gif_image = Image.open(BytesIO(img_bytes))
    # gif_image.seek(0)
    jpg_image = gif_image.convert('RGB')
    jpg_bytes = BytesIO()
    jpg_bytes.name = 'price.jpg'
    jpg_image.save(jpg_bytes, format='JPEG')
    # jpg_bytes.seek(0)
    return jpg_bytes
