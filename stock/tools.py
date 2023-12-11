from time import time as timestamp
from datetime import datetime, time


def is_trading_day() -> bool:
    now = datetime.now()
    if now.weekday() >= 5:
        return False
    return True


def is_trading_time() -> bool:
    if not is_trading_day():
        return False
    now = datetime.now().time()
    morning_start = time(9, 30)
    morning_end = time(11, 30)
    afternoon_start = time(13, 0)
    afternoon_end = time(15, 0)
    return morning_start <= now <= morning_end or afternoon_start <= now <= afternoon_end


class StockData:
    def __init__(self):
        self.stock_summary = ''
        self.updown_bar = ''
        self.price_img_id = ''
        self.last_timestamp = 0
        self.trading = None

    def save(self, stock_summary: str, updown_bar: str, price_img_id: str):
        self.stock_summary = stock_summary
        self.updown_bar = updown_bar
        self.price_img_id = price_img_id
        self.last_timestamp = int(timestamp())
        self.trading = is_trading_time()
