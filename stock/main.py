import os
import asyncio
import aiohttp
from PIL import Image
from io import BytesIO
from common.data import *
from stock.format import *
from datetime import datetime, time


async def get_stock_summary(trading: bool = None):
    sh_raw, sz_raw, cyb_raw = await asyncio.gather(
        get_raw_price('sh000001'),
        get_raw_price('sz399001'),
        get_raw_price('sz399006')
    )
    sh_d = get_stock_details(sh_raw)
    sz_d = get_stock_details(sz_raw)
    cyb_d = get_stock_details(cyb_raw)
    sh_sum = get_detailed_summary(sh_d, trading)
    sz_sum = get_stock_short_summary(sz_d)
    cyb_sum = get_stock_short_summary(cyb_d)
    stock_summary = (
        f'{sh_sum}\n深 {sz_sum}\n创 {cyb_sum}'
    )
    return stock_summary


async def query_data(trading: bool = None) -> tuple:
    stock_summary, raw_updown, price_img = await asyncio.gather(
        get_stock_summary(trading),
        get_raw_updown(),
        get_price_img('sh000001')
    )
    updown_bar = get_updown_bar(get_updown(raw_updown))
    return stock_summary, updown_bar, price_img


async def get_cache(trading: bool = None) -> tuple:
    price_img = None
    price_img_id = ''
    if all([
        os.path.isfile(f'{STOCK_DATA_PATH}/{STOCK_DATA_SUMMARY}'),
        os.path.isfile(f'{STOCK_DATA_PATH}/{STOCK_DATA_UPDOWN}'),
        os.path.isfile(f'{STOCK_DATA_PATH}/{STOCK_DATA_PRICE_IMG}')
    ]):
        with open(f'{STOCK_DATA_PATH}/{STOCK_DATA_SUMMARY}', 'r', encoding='utf-8') as f:
            stock_summary = f.read()
        with open(f'{STOCK_DATA_PATH}/{STOCK_DATA_UPDOWN}', 'r', encoding='utf-8') as f:
            updown_bar = f.read()
        with open(f'{STOCK_DATA_PATH}/{STOCK_DATA_PRICE_IMG}', 'r', encoding='utf-8') as f:
            price_img_id = f.read()
        return stock_summary, updown_bar, price_img, price_img_id
    else:
        raw_data = await query_data(trading)
        stock_summary, updown_bar, price_img = raw_data
        return stock_summary, updown_bar, price_img, price_img_id


async def query(trading: bool = None, no_cache: bool = False) -> tuple:
    price_img_id = ''
    if trading is None:
        trading = is_trading_time()
    if trading or no_cache:
        raw_data = await query_data(trading)
        stock_summary, updown_bar, price_img = raw_data
        # no need to save cache
    else:
        stock_summary, updown_bar, price_img, price_img_id = await get_cache(trading)
    return stock_summary, updown_bar, price_img, price_img_id
