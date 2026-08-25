import io
import os
import pickle
import logging
from typing import Dict, Optional
from telethon.tl.types import User
from time import time as timestamp
from datetime import time, datetime
from chinese_calendar import is_holiday
from share.common import get_user_name
from common.data import STOCK_DATA_DIR, STOCK_REMINDER_FILE


def is_trading_day(date: datetime = None) -> bool:
    date = date or datetime.now()
    is_weekend = date.weekday() >= 5
    if is_weekend or is_holiday(date):
        return False
    return True


def is_trading_time(query_time: datetime = None) -> bool:
    query_time = query_time or datetime.now()
    if not is_trading_day(query_time):
        return False
    now = query_time.time()
    morning_start = time(9, 30)
    morning_end = time(11, 30)
    afternoon_start = time(13, 0)
    afternoon_end = time(15, 0)
    return morning_start <= now <= morning_end or afternoon_start <= now <= afternoon_end


class StockData:
    """
    Cached chart, kept as raw bytes.

    Telethon has no Bot API file_id to hold on to, so the picture itself
    is cached and re-uploaded; it is only a few tens of KB.
    """
    def __init__(self):
        self.stock_summary = ''
        self.updown_bar = ''
        self.price_img: Optional[bytes] = None
        self.last_timestamp = 0
        self.trading = None

    def save(self, stock_summary: str, updown_bar: str, price_img: bytes):
        self.stock_summary = stock_summary
        self.updown_bar = updown_bar
        self.price_img = price_img
        self.last_timestamp = int(timestamp())
        self.trading = is_trading_time()


class _LegacyPyrogramObject:
    """
    Stand-in that lets a reminder file written by the pyrogram build be
    read back. Only `id`, `first_name` and `last_name` are used.
    """
    def __init__(self, *args, **kwargs):
        pass

    def __setstate__(self, state):
        if isinstance(state, dict):
            self.__dict__.update(state)


class _LegacyUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if module.startswith('pyrogram'):
            return _LegacyPyrogramObject
        return super().find_class(module, name)


class StockReminder:
    """
    Who wants a closing-bell reminder, as {chat_id: {user_id: name}}.

    Telethon `User` objects hold a live client and are awkward to
    persist, and the name is all we need to build a mention.
    """
    def __init__(self, file: str = f'{STOCK_DATA_DIR}/{STOCK_REMINDER_FILE}'):
        self.data: Dict[int, Dict[int, str]] = {}
        # 好好好 https://t.me/rkmiu/113097
        self.load(file)

    def add(self, chat_id: int, user: User) -> bool:
        users = self.data.setdefault(chat_id, {})
        if user.id in users:
            return False
        users[user.id] = get_user_name(user)
        self.save()
        return True

    def remove(self, chat_id: int, user: User) -> bool:
        # https://t.me/teasps/6789
        users = self.data.get(chat_id)
        if not users or user.id not in users:
            return False
        del users[user.id]
        if not users:
            del self.data[chat_id]
        self.save()
        return True

    def load(self, file: str = f'{STOCK_DATA_DIR}/{STOCK_REMINDER_FILE}'):
        if not os.path.exists(file):
            return
        with open(file, 'rb') as f:
            raw = f.read()
        migrated = False
        try:
            data = pickle.loads(raw)
        except ModuleNotFoundError:
            logging.warning('[stock]	Migrating reminders written by the pyrogram build')
            data = _LegacyUnpickler(io.BytesIO(raw)).load()
            migrated = True
        self.data = {
            chat_id: {u.id: get_user_name(u) for u in users} if isinstance(users, list) else users
            for chat_id, users in data.items()
        }
        if migrated:
            self.save(file)

    def save(self, file: str = f'{STOCK_DATA_DIR}/{STOCK_REMINDER_FILE}'):
        with open(file, 'wb') as f:
            pickle.dump(self.data, f)


def invest_suggestion(price: float, base_price: int = 4000, price_interval: int = 100) -> str:
    if price < base_price - price_interval:
        return '木夋口合' + '！' * int((base_price - price_interval - price) / 100)
    elif price < base_price:
        return '适当加仓'
    elif price < base_price + price_interval:
        return '持仓观望'
    elif price < base_price + 2 * price_interval:
        return '适当减仓'
    else:
        return '忄夬足包' + '！ ' * int((price - (base_price + 2 * price_interval)) / 100)
