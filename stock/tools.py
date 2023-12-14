import os
import pickle
from typing import Dict, List
from pyrogram.types import User
from time import time as timestamp
from datetime import datetime, time
from common.data import STOCK_DATA_DIR, STOCK_REMINDER_FILE


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


class StockReminder:
    def __init__(self, file: str = f'{STOCK_DATA_DIR}/{STOCK_REMINDER_FILE}'):
        self.data: Dict[int, List[User]] = {}
        # 好好好 https://t.me/rkmiu/113097
        self.load(file)

    def add(self, chat_id: int, user: User) -> bool:
        if chat_id not in self.data:
            self.data[chat_id] = []
        if user.id not in [u.id for u in self.data[chat_id]]:
            self.data[chat_id].append(user)
            self.save()
            return True
        return False

    def remove(self, chat_id: int, user: User) -> bool:
        if chat_id in self.data and user.id in [u.id for u in self.data[chat_id]]:
            self.data[chat_id].remove(user)
            if not self.data[chat_id]:
                del self.data[chat_id]
            self.save()
            return True
        return False

    def load(self, file: str = f'{STOCK_DATA_DIR}/{STOCK_REMINDER_FILE}'):
        if os.path.exists(file):
            with open(file, 'rb') as f:
                self.data = pickle.load(f)

    def save(self, file: str = f'{STOCK_DATA_DIR}/{STOCK_REMINDER_FILE}'):
        with open(file, 'wb') as f:
            pickle.dump(self.data, f)
