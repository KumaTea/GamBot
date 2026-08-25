import asyncio
from time import time
from typing import Optional, Tuple
from common.data import SZ_URL, CYB_URL
from stock.quote import Quote, normalize
from stock.tools import StockData, StockReminder, is_trading_time, invest_suggestion
from stock.req import get_price_img, get_quote, get_quotes, get_raw_updown
from stock.format import (
    get_detailed_summary, get_stock_short_summary,
    get_updown, get_updown_bar
)


SH, SZ, CYB = 'sh000001', 'sz399001', 'sz399006'
INDEX_CODES = [SH, SZ, CYB]

# how long a quote stays worth reusing, open and closed
FRESH_TRADING = 30
FRESH_CLOSED = 2 * 60 * 60

stock_cache = StockData()
stock_reminder = StockReminder()


class QuoteCache:
    """
    Last quote seen per symbol.

    A group that all asks about the same stock at once should cost one
    request, not one each.
    """
    def __init__(self):
        self.quotes: dict[str, Tuple[float, Quote]] = {}

    def get(self, code: str) -> Optional[Quote]:
        entry = self.quotes.get(code)
        if not entry:
            return None
        when, quote = entry
        ttl = FRESH_TRADING if is_trading_time() else FRESH_CLOSED
        return quote if time() - when < ttl else None

    def put(self, code: str, quote: Quote):
        self.quotes[code] = (time(), quote)


quote_cache = QuoteCache()


async def get_stock_summary(trading: bool = None) -> str:
    quotes = await get_quotes(INDEX_CODES)
    sh, sz, cyb = quotes[SH], quotes[SZ], quotes[CYB]
    if not sh:
        return '行情暂时取不到。'

    if trading is None:
        trading = is_trading_time()
    if trading:
        trading_info = '当前股市 **交易中**\n'
        suggestion = f'\n投资建议：**{invest_suggestion(sh.price)}**'
    else:
        trading_info = '当前股市 **已休市**\n'
        suggestion = ''

    lines = [trading_info, get_detailed_summary(sh, trading)]
    if sz:
        lines.append(f'[深]({SZ_URL}) {get_stock_short_summary(sz)}')
    if cyb:
        lines.append(f'[创]({CYB_URL}) {get_stock_short_summary(cyb)}')
    return '\n'.join(lines) + suggestion


async def query_data(trading: bool = None) -> Tuple[str, str, Optional[bytes]]:
    stock_summary, raw_updown, price_img = await asyncio.gather(
        get_stock_summary(trading),
        get_raw_updown(),
        get_price_img(SH)
    )
    updown_bar = get_updown_bar(get_updown(raw_updown)) if raw_updown else ''
    # the chart is cached as bytes: Telethon has no file_id to hold on to,
    # and it is only a few tens of KB
    stock_cache.save(stock_summary, updown_bar, price_img)
    return stock_summary, updown_bar, price_img


async def get_cache(trading: bool = None) -> Tuple[str, str, Optional[bytes]]:
    if stock_cache.stock_summary and stock_cache.price_img:
        return stock_cache.stock_summary, stock_cache.updown_bar, stock_cache.price_img
    return await query_data(trading)


async def query(trading: bool = None, no_cache: bool = False) -> Tuple[str, str, Optional[bytes]]:
    if trading is None:
        trading = is_trading_time()
    if trading or no_cache:
        return await query_data(trading)
    return await get_cache(trading)


async def query_symbol(text: str, want_chart: bool = True):
    """
    One symbol, by whatever the user called it.

    Returns (code, quote, chart). A code with no quote means Sina knows
    nothing about it; no code at all means it was not a symbol.
    """
    code = normalize(text)
    if not code:
        return None, None, None

    quote = quote_cache.get(code)
    if quote and not want_chart:
        return code, quote, None

    if quote:
        chart = await get_price_img(code)
        return code, quote, chart

    if want_chart:
        quote, chart = await asyncio.gather(get_quote(code), get_price_img(code))
    else:
        quote, chart = await get_quote(code), None

    if quote:
        quote_cache.put(code, quote)
    return code, quote, chart


async def price_of(code: str) -> Optional[Quote]:
    """A quote good enough to deal on -- cached only very briefly."""
    quote = quote_cache.get(code)
    if quote:
        return quote
    quote = await get_quote(code)
    if quote:
        quote_cache.put(code, quote)
    return quote
