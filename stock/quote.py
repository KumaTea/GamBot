import re
from typing import Optional
from dataclasses import dataclass


CN, HK, US = 'cn', 'hk', 'us'

CURRENCY = {CN: '¥', HK: 'HK$', US: '$'}

# what people actually type when they mean an index
ALIASES = {
    '上证': 'sh000001', '上证指数': 'sh000001', '大盘': 'sh000001', 'sh': 'sh000001',
    '深证': 'sz399001', '深成指': 'sz399001', 'sz': 'sz399001',
    '创业板': 'sz399006', '创业板指': 'sz399006', 'cyb': 'sz399006',
    '科创50': 'sh000688', '沪深300': 'sh000300', '中证500': 'sh000905',
    '恒生': 'hkHSI', '恒生指数': 'hkHSI', 'hsi': 'hkHSI',
    '国企指数': 'hkHSCEI', '恒生科技': 'hkHSTECH',
    '道琼斯': 'gb_$dji', '道指': 'gb_$dji',
    '纳斯达克': 'gb_$ixic', '纳指': 'gb_$ixic',
    '标普': 'gb_$inx', '标普500': 'gb_$inx',
}

# Shanghai has 60/68 (and 9/5 for B shares and funds); Shenzhen has
# 00/30/20/15; Beijing took over the old NEEQ 43/83/87 and adds 92.
# `000001` is both 上证指数 and 平安银行 -- a bare six-digit code is read
# as the stock, and the index has an alias above.
SH_PREFIXES = ('60', '68', '90', '50', '51', '58', '11', '13')
SZ_PREFIXES = ('00', '30', '20', '15', '16', '18', '12', '39')
BJ_PREFIXES = ('43', '83', '87', '88', '92')


def normalize(text: str) -> Optional[str]:
    """
    Turn whatever someone typed into the code Sina wants.

    Returns None when it does not look like a stock at all, which is
    the caller's cue to say so rather than to fetch nonsense.
    """
    text = (text or '').strip()
    if not text:
        return None

    lowered = text.lower()
    if lowered in ALIASES:
        return ALIASES[lowered]
    if text in ALIASES:
        return ALIASES[text]

    # already a sina code
    if re.fullmatch(r'(sh|sz|bj)\d{6}', lowered):
        return lowered
    if re.fullmatch(r'hk\d{5}', lowered):
        return lowered
    if lowered.startswith('gb_'):
        return lowered

    # 600519.SH / 00700.HK, the way a terminal writes it
    dotted = re.fullmatch(r'(\d{5,6})\.(sh|sz|bj|hk)', lowered)
    if dotted:
        digits, market = dotted.groups()
        return f'{market}{digits}'

    if re.fullmatch(r'\d{6}', lowered):
        return f'{a_share_market(lowered)}{lowered}'
    if re.fullmatch(r'\d{1,5}', lowered):
        # Hong Kong codes are five digits, zero padded
        return f'hk{lowered.zfill(5)}'
    if re.fullmatch(r'[a-z][a-z.\-]{0,7}', lowered):
        return f'gb_{lowered}'
    return None


def a_share_market(digits: str) -> str:
    if digits.startswith(SH_PREFIXES):
        return 'sh'
    if digits.startswith(BJ_PREFIXES):
        return 'bj'
    if digits.startswith(SZ_PREFIXES):
        return 'sz'
    # 39xxxx indices sit in Shenzhen, everything unknown is a fair guess
    return 'sz'


def market_of(code: str) -> str:
    if code.startswith('hk'):
        return HK
    if code.startswith('gb_'):
        return US
    return CN


def display_symbol(code: str) -> str:
    """The code as a person would write it back."""
    if code.startswith(('sh', 'sz', 'bj')):
        return code[2:]
    if code.startswith('hk'):
        return code[2:]
    if code.startswith('gb_'):
        return code[3:].upper()
    return code


@dataclass
class Quote:
    code: str
    name: str
    market: str
    price: float
    prev_close: float
    open: float
    high: float
    low: float
    volume: float = 0
    amount: float = 0
    when: str = ''

    @property
    def change(self) -> float:
        return self.price - self.prev_close

    @property
    def percent(self) -> float:
        return self.change / self.prev_close if self.prev_close else 0

    @property
    def symbol(self) -> str:
        return display_symbol(self.code)

    @property
    def currency(self) -> str:
        return CURRENCY[self.market]

    @property
    def tradeable(self) -> bool:
        """A price you could actually deal at -- not a suspended stock."""
        return self.price > 0


def parse(code: str, raw: str) -> Optional[Quote]:
    """
    Read one of Sina's comma-separated quote lines.

    The three markets have three different layouts and Sina documents
    none of them, so each gets its own reader.
    """
    if not raw:
        return None
    market = market_of(code)
    fields = raw.split(',')
    try:
        if market == CN:
            return parse_cn(code, fields)
        if market == HK:
            return parse_hk(code, fields)
        return parse_us(code, fields)
    except (IndexError, ValueError):
        return None


def parse_cn(code: str, f: list) -> Optional[Quote]:
    if len(f) < 10:
        return None
    return Quote(
        code=code,
        name=f[0],
        market=CN,
        open=float(f[1]),
        prev_close=float(f[2]),
        price=float(f[3]),
        high=float(f[4]),
        low=float(f[5]),
        volume=float(f[8]),
        amount=float(f[9]),
        when=f'{f[30]} {f[31]}' if len(f) > 31 else '',
    )


def parse_hk(code: str, f: list) -> Optional[Quote]:
    if len(f) < 13:
        return None
    return Quote(
        code=code,
        name=f[1] or f[0],
        market=HK,
        open=float(f[2]),
        prev_close=float(f[3]),
        high=float(f[4]),
        low=float(f[5]),
        price=float(f[6]),
        amount=float(f[11]),
        volume=float(f[12]),
        when=f'{f[17]} {f[18]}' if len(f) > 18 else '',
    )


def parse_us(code: str, f: list) -> Optional[Quote]:
    if len(f) < 8:
        return None
    price = float(f[1])
    change = float(f[4])
    return Quote(
        code=code,
        name=f[0],
        market=US,
        price=price,
        prev_close=price - change,
        open=float(f[5]),
        high=float(f[6]),
        low=float(f[7]),
        volume=float(f[10]) if len(f) > 10 and f[10] else 0,
        when=f[3],
    )


def quote_link(code: str) -> str:
    """The eastmoney page for a symbol, for the message to link to."""
    symbol = display_symbol(code)
    market = market_of(code)
    if market == HK:
        return f'https://quote.eastmoney.com/hk/{symbol}.html'
    if market == US:
        return f'https://quote.eastmoney.com/us/{symbol.lstrip("$")}.html'
    # mainland indices live under a `zs` prefix, shares under their own
    if is_index(code):
        return f'https://quote.eastmoney.com/zs{symbol}.html'
    return f'https://quote.eastmoney.com/{code}.html'


def is_index(code: str) -> bool:
    """
    Mainland index codes, which are not stocks and cannot be bought.

    Shanghai numbers its indices 000xxx and 950xxx, Shenzhen uses 399xxx.
    """
    symbol = display_symbol(code)
    if code.startswith('sh'):
        return symbol.startswith(('000', '950'))
    if code.startswith('sz'):
        return symbol.startswith('399')
    return False
