import os
from common.data import *
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


def save_cache(stock_summary: str, updown_bar: str, price_img_id: str):
    with open(f'{STOCK_DATA_PATH}/{STOCK_DATA_SUMMARY}', 'w', encoding='utf-8') as f:
        f.write(stock_summary)
    with open(f'{STOCK_DATA_PATH}/{STOCK_DATA_UPDOWN}', 'w', encoding='utf-8') as f:
        f.write(updown_bar)
    with open(f'{STOCK_DATA_PATH}/{STOCK_DATA_PRICE_IMG}', 'w', encoding='utf-8') as f:
        f.write(price_img_id)


def clear_cache():
    for file in os.listdir(STOCK_DATA_PATH):
        os.remove(f'{STOCK_DATA_PATH}/{file}')
