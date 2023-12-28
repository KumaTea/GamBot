from stock.tools import is_trading_time
from common.data import RISE_ICON, FALL_ICON, UP_ICON, DOWN_ICON, STILL_ICON, SH_URL


def get_stock_details(raw_price: str) -> dict:
    raw_price_list = raw_price.split(',')
    stock_details = {
        '名称': raw_price_list[0],
        '今开': float(raw_price_list[1]),
        '昨收': float(raw_price_list[2]),
        '当前': float(raw_price_list[3]),
        '最高': float(raw_price_list[4]),
        '最低': float(raw_price_list[5]),
        # '买一': float(raw_price_list[6]),
        # '卖一': float(raw_price_list[7]),
        '成交量': float(raw_price_list[8]),
        '成交额': float(raw_price_list[9]),
        # '时间': raw_price_list[31],
    }

    stock_details['涨跌'] = stock_details['当前'] - stock_details['昨收']
    stock_details['涨跌幅'] = stock_details['涨跌'] / stock_details['昨收']
    return stock_details


def get_detailed_summary(stock_details: dict, trading: bool = None) -> str:
    if trading is None:
        trading = is_trading_time()
    message = f'[上证指数]({SH_URL})'
    if trading:
        message += '当前 {PRICE_INFO}\n'
    else:
        message += '收盘时 {PRICE_INFO}\n'
    message += '{HISTORY_INFO}\n{PEAK_INFO}\n'
    fluctuation = RISE_ICON if stock_details['涨跌'] > 0 else FALL_ICON
    price_info = '**{当前:.2f}**\n{FL} {涨跌:.2f} {涨跌幅:.2%}'.format(
        当前=stock_details['当前'],
        涨跌=stock_details['涨跌'],
        涨跌幅=stock_details['涨跌幅'],
        FL=fluctuation
    )
    history_info = '今开 {今开:.2f} 昨收 {昨收:.2f}'.format(**stock_details)
    peak_info = '最高 {最高:.2f} 最低 {最低:.2f}'.format(**stock_details)
    message = message.format(PRICE_INFO=price_info, HISTORY_INFO=history_info, PEAK_INFO=peak_info)
    return message


def get_stock_short_summary(stock_details: dict) -> str:
    fluctuation = RISE_ICON if stock_details['涨跌'] > 0 else FALL_ICON
    message = '{当前:.2f} {FL} {涨跌幅:.2%}'.format(
        当前=stock_details['当前'],
        涨跌幅=stock_details['涨跌幅'],
        FL=fluctuation
    )
    return message


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
    up_len = round(up / total * bar_len)
    down_len = round(down / total * bar_len)
    still_len = bar_len - up_len - down_len
    up_bar = UP_ICON * up_len
    down_bar = DOWN_ICON * down_len
    still_bar = STILL_ICON * still_len
    return up_bar + still_bar + down_bar
