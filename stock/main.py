import asyncio
from io import BytesIO
from typing import Tuple, Optional
from stock.tools import StockData, StockReminder, is_trading_time, invest_suggestion
from stock.req import get_raw_price, get_raw_updown, get_price_img
from stock.format import get_stock_details, get_detailed_summary, get_stock_short_summary, get_updown_bar, get_updown


stock_cache = StockData()
stock_reminder = StockReminder()


async def get_stock_summary(trading: bool = None) -> str:
    if trading is None:
        trading = is_trading_time()
    if trading:
        trading_info = '当前股市 **交易中**\n'
    else:
        trading_info = '当前股市 **已休市**\n'
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
    if trading:
        sh_price = sh_d['当前']
        suggestion = f'\n投资建议：**{invest_suggestion(sh_price)}**'
    else:
        suggestion = ''
    stock_summary = (
        f'{trading_info}\n'
        f'{sh_sum}\n'
        f'深 {sz_sum}\n'
        f'创 {cyb_sum}\n'
        f'{suggestion}'
    )
    return stock_summary


async def query_data(trading: bool = None) -> Tuple[str, str, BytesIO]:
    stock_summary, raw_updown, price_img = await asyncio.gather(
        get_stock_summary(trading),
        get_raw_updown(),
        get_price_img('sh000001')
    )
    updown_bar = get_updown_bar(get_updown(raw_updown))
    return stock_summary, updown_bar, price_img


async def get_cache(trading: bool = None) -> Tuple[str, str, Optional[BytesIO], Optional[str]]:
    price_img = None
    stock_summary = stock_cache.stock_summary
    updown_bar = stock_cache.updown_bar
    price_img_id = stock_cache.price_img_id
    if all([stock_summary, updown_bar, price_img_id]):
        return stock_summary, updown_bar, price_img, price_img_id
    else:
        raw_data = await query_data(trading)
        stock_summary, updown_bar, price_img = raw_data
        return stock_summary, updown_bar, price_img, price_img_id


async def query(trading: bool = None, no_cache: bool = False) -> Tuple[str, str, Optional[BytesIO], Optional[str]]:
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
