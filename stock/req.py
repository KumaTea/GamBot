import aiohttp
import logging
from typing import Dict, List, Optional
from stock.quote import CN, HK, US, Quote, market_of, parse
from common.data import (
    SINA_HEADER, STOCK_PRICE_API, STOCK_PRICE_IMG,
    STOCK_PRICE_IMG_HK, STOCK_PRICE_IMG_US, UPDOWN_API
)


REQUEST_TIMEOUT = 10


async def sina_text(url: str) -> str:
    """
    Fetch one of Sina's javascript quote blobs.

    Sina answers in GBK and does not always say so, so the encoding is
    not left to be guessed.
    """
    timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, headers=SINA_HEADER) as resp:
                return await resp.text(encoding='gbk', errors='replace')
    except Exception as e:
        logging.warning(f'[stock]\tCould not read {url}: {e}')
        return ''


def unpack(text: str) -> Dict[str, str]:
    """`var hq_str_sh000001="...";` for each line, as {code: payload}."""
    quotes = {}
    for line in text.split(';'):
        line = line.strip()
        if not line.startswith('var hq_str_'):
            continue
        name, _, payload = line.partition('=')
        code = name[len('var hq_str_'):].strip()
        quotes[code] = payload.strip().strip('"')
    return quotes


async def get_raw_price(stock_code: str) -> str:
    raw = await sina_text(STOCK_PRICE_API.format(STOCK_CODE=stock_code))
    return unpack(raw).get(stock_code, '')


async def get_quotes(codes: List[str]) -> Dict[str, Optional[Quote]]:
    """Every code in one request -- Sina takes them comma separated."""
    if not codes:
        return {}
    raw = await sina_text(STOCK_PRICE_API.format(STOCK_CODE=','.join(codes)))
    payloads = unpack(raw)
    return {code: parse(code, payloads.get(code, '')) for code in codes}


async def get_quote(code: str) -> Optional[Quote]:
    return (await get_quotes([code])).get(code)


async def get_raw_updown() -> list:
    text = await sina_text(UPDOWN_API)
    return [payload for payload in unpack(text).values() if payload]


def chart_url(code: str) -> str:
    """The intraday chart Sina draws for a symbol."""
    market = market_of(code)
    if market == HK:
        return STOCK_PRICE_IMG_HK.format(STOCK_CODE=code[2:])
    if market == US:
        return STOCK_PRICE_IMG_US.format(STOCK_CODE=code[3:].lstrip('$'))
    return STOCK_PRICE_IMG.format(STOCK_CODE=code)


async def get_price_img(stock_code: str) -> Optional[bytes]:
    timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
    url = chart_url(stock_code)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, headers=SINA_HEADER) as resp:
                if resp.status != 200:
                    logging.warning(f'[stock]\t{url} returned HTTP {resp.status}')
                    return None
                return await resp.read()
    except Exception as e:
        logging.warning(f'[stock]\tCould not read chart {url}: {e}')
        return None


# `CN` is imported for callers that want the market constants alongside
# the requests; keeping it re-exported saves them a second import.
__all__ = [
    'CN', 'HK', 'US',
    'chart_url', 'get_price_img', 'get_quote', 'get_quotes',
    'get_raw_price', 'get_raw_updown', 'sina_text', 'unpack',
]
