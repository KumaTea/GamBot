from stock.quote import CN, Quote
from stock.tools import is_trading_time
from common.data import SH_URL, UP_ICON, DOWN_ICON, FALL_ICON, RISE_ICON, STILL_ICON


def arrow(change: float) -> str:
    if change > 0:
        return RISE_ICON
    if change < 0:
        return FALL_ICON
    return STILL_ICON


def human_number(value: float) -> str:
    """Chinese scale: 万 at ten thousand, 亿 at a hundred million."""
    if value >= 100000000:
        return f'{value / 100000000:.2f} 亿'
    if value >= 10000:
        return f'{value / 10000:.2f} 万'
    return f'{value:.0f}'


def turnover(quote: Quote) -> str:
    """Shares traded and money changed hands, as the market reports them."""
    if not (quote.volume or quote.amount):
        return ''
    parts = []
    if quote.volume:
        # the mainland counts in lots of a hundred, everywhere else in shares
        lots = quote.volume / 100 if quote.market == CN else quote.volume
        unit = '手' if quote.market == CN else '股'
        parts.append(f'{human_number(lots)}{unit}')
    if quote.amount:
        parts.append(f'{quote.currency}{human_number(quote.amount)}')
    return '成交 ' + ' / '.join(parts)


def price_text(quote: Quote) -> str:
    """Penny stocks need the third decimal; blue chips do not."""
    digits = 3 if 0 < quote.price < 10 else 2
    return f'**{quote.currency}{quote.price:.{digits}f}**'


def format_quote(quote: Quote, link: str = None) -> str:
    """One symbol, in full."""
    title = f'**{quote.name}**（{quote.symbol}）'
    if link:
        title = f'[{quote.name}]({link})（{quote.symbol}）'

    if not quote.tradeable:
        return f'{title}\n当前无报价（停牌或未开盘）'

    lines = [
        title,
        price_text(quote),
        f'{arrow(quote.change)} {quote.change:+.2f} {quote.percent:+.2%}',
        f'今开 {quote.open:.2f}　昨收 {quote.prev_close:.2f}',
        f'最高 {quote.high:.2f}　最低 {quote.low:.2f}',
    ]
    flow = turnover(quote)
    if flow:
        lines.append(flow)
    if quote.when:
        lines.append(f'`{quote.when}`')
    return '\n'.join(lines)


def get_detailed_summary(quote: Quote, trading: bool = None) -> str:
    if trading is None:
        trading = is_trading_time()
    when = '当前' if trading else '收盘'
    return (
        f'[{quote.name}]({SH_URL}){when} **{quote.price:.2f}**\n'
        f'{arrow(quote.change)} {quote.change:.2f} {quote.percent:.2%}\n'
        f'今开 {quote.open:.2f} 昨收 {quote.prev_close:.2f}\n'
        f'最高 {quote.high:.2f} 最低 {quote.low:.2f}\n'
    )


def get_stock_short_summary(quote: Quote) -> str:
    return f'{quote.price:.2f} {arrow(quote.change)} {quote.percent:.2%}'


def get_updown(raw_updown: list) -> tuple:
    up, down, still = [], [], []
    for item in raw_updown:
        u, d, s = map(int, item.split(','))
        up.append(u)
        down.append(d)
        still.append(s)
    return sum(up), sum(down), sum(still)


def get_updown_bar(updown: tuple, bar_len: int = 12) -> str:
    up, down, still = updown
    total = up + down + still
    if not total:
        return ''
    up_len = round(up / total * bar_len)
    down_len = round(down / total * bar_len)
    still_len = max(0, bar_len - up_len - down_len)
    return UP_ICON * up_len + STILL_ICON * still_len + DOWN_ICON * down_len


def missing(symbol: str) -> str:
    return f'查不到 `{symbol}`，试试股票代码，比如 `/stock 600519`。'
