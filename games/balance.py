import os
import pickle
import logging
from datetime import date
from typing import Dict, List, Tuple


BALANCE_DATA_DIR = 'data/games'
BALANCE_DATA_FILE = 'balance.p'
CHECKIN_DATA_FILE = 'checkin.p'
PNL_DATA_FILE = 'pnl.p'

HOUSE = 0                  # the bank's own seat; no account has id 0

STARTING_BALANCE = 10000   # what a new player is handed
MINIMUM_BALANCE = 10       # 救济金起点
WELFARE_AMOUNT = 1000      # 救济金金额
CHECKIN_AMOUNT = 500       # 每日签到
CHECKIN_STREAK_BONUS = 100  # per consecutive day, capped
CHECKIN_STREAK_CAP = 10


def ensure_data_dir():
    os.makedirs(BALANCE_DATA_DIR, exist_ok=True)


def fmt_balance(amount: int | float) -> float:
    """Money, to the cent."""
    return round(amount, 2)


def money(amount: int | float) -> str:
    """Money as it should be read: no trailing `.0` on whole numbers."""
    amount = fmt_balance(amount)
    if amount == int(amount):
        return f'{int(amount):,}'
    return f'{amount:,.2f}'


def signed(amount: int | float) -> str:
    """Money with the sign kept -- a profit only reads as one with it."""
    amount = fmt_balance(amount)
    return f'+{money(amount)}' if amount > 0 else money(amount)


class UserBalance:
    def __init__(self):
        self.balances: Dict[int, float] = {}
        ensure_data_dir()
        self.load()

    @property
    def file_path(self) -> str:
        return f'{BALANCE_DATA_DIR}/{BALANCE_DATA_FILE}'

    def get_balance(self, user_id: int) -> float:
        """A player's money, opening an account for a newcomer."""
        if user_id not in self.balances:
            self.balances[user_id] = fmt_balance(STARTING_BALANCE)
            self.save()
        return self.balances[user_id]

    def set_balance(self, user_id: int, amount: int | float):
        self.balances[user_id] = fmt_balance(amount)
        self.save()

    def add_balance(self, user_id: int, amount: int | float) -> float:
        new_balance = fmt_balance(self.get_balance(user_id) + amount)
        self.set_balance(user_id, new_balance)
        return new_balance

    def subtract_balance(self, user_id: int, amount: int | float) -> bool:
        """Take money off a player. False -- and no change -- if short."""
        current = self.get_balance(user_id)
        if current < amount:
            return False
        self.set_balance(user_id, current - amount)
        return True

    def transfer(self, sender: int, receiver: int, amount: int | float) -> bool:
        if sender == receiver or amount <= 0:
            return False
        if not self.subtract_balance(sender, amount):
            return False
        self.add_balance(receiver, amount)
        return True

    def top(self, count: int = 10) -> List[Tuple[int, float]]:
        return sorted(self.balances.items(), key=lambda kv: kv[1], reverse=True)[:count]

    def rank_of(self, user_id: int) -> int:
        """1-based position on the leaderboard."""
        balance = self.get_balance(user_id)
        return sum(1 for b in self.balances.values() if b > balance) + 1

    def load(self):
        if not os.path.isfile(self.file_path):
            return
        try:
            with open(self.file_path, 'rb') as f:
                self.balances = pickle.load(f)
        except Exception as e:
            logging.error(f'[games]\tCould not read balances: {e}')
            self.balances = {}

    def save(self):
        with open(self.file_path, 'wb') as f:
            pickle.dump(self.balances, f)


class ProfitAndLoss:
    """
    What each player is up or down at the tables.

    Only a wager moves this. An allowance, a transfer or a top-up
    changes what somebody has without anybody having won it, and a
    number that counts those is a record of generosity rather than of
    play. The bank keeps a seat here too, holding the mirror image of
    everyone else's: every chip a player wins is a chip the house lost,
    so the two always add up to nothing.
    """
    def __init__(self):
        self.pnl: Dict[int, float] = {}
        ensure_data_dir()
        self.load()

    @property
    def file_path(self) -> str:
        return f'{BALANCE_DATA_DIR}/{PNL_DATA_FILE}'

    def get(self, user_id: int) -> float:
        return self.pnl.get(user_id, 0.0)

    @property
    def house(self) -> float:
        """What the bank is up, which is what the players are down."""
        return self.get(HOUSE)

    def record(self, user_id: int, profit: int | float) -> float:
        """Book one settled wager, and its opposite against the bank."""
        booked = fmt_balance(self.get(user_id) + profit)
        self.pnl[user_id] = booked
        self.pnl[HOUSE] = fmt_balance(self.get(HOUSE) - profit)
        self.save()
        return booked

    def players(self) -> Dict[int, float]:
        """Everyone who has played, the house not being a player."""
        return {u: p for u, p in self.pnl.items() if u != HOUSE}

    def top(self, count: int = 10) -> List[Tuple[int, float]]:
        return sorted(self.players().items(), key=lambda kv: kv[1], reverse=True)[:count]

    def load(self):
        if not os.path.isfile(self.file_path):
            return
        try:
            with open(self.file_path, 'rb') as f:
                self.pnl = pickle.load(f)
        except Exception as e:
            logging.error(f'[games]\tCould not read profit and loss: {e}')
            self.pnl = {}

    def save(self):
        with open(self.file_path, 'wb') as f:
            pickle.dump(self.pnl, f)


class CheckIn:
    """Who has collected their daily allowance, and for how many days running."""
    def __init__(self):
        self.data: Dict[int, Tuple[str, int]] = {}  # user_id -> (iso date, streak)
        ensure_data_dir()
        self.load()

    @property
    def file_path(self) -> str:
        return f'{BALANCE_DATA_DIR}/{CHECKIN_DATA_FILE}'

    def claim(self, user_id: int) -> Tuple[bool, int, float]:
        """
        Try to collect today's allowance.

        Returns (collected, streak, amount). A day missed resets the
        streak; collecting twice in one day does nothing.
        """
        today = date.today()
        last, streak = self.data.get(user_id, ('', 0))
        if last == today.isoformat():
            return False, streak, 0

        yesterday = date.fromordinal(today.toordinal() - 1).isoformat()
        streak = streak + 1 if last == yesterday else 1
        self.data[user_id] = (today.isoformat(), streak)
        self.save()

        bonus = CHECKIN_STREAK_BONUS * min(streak, CHECKIN_STREAK_CAP)
        return True, streak, CHECKIN_AMOUNT + bonus

    def load(self):
        if not os.path.isfile(self.file_path):
            return
        try:
            with open(self.file_path, 'rb') as f:
                self.data = pickle.load(f)
        except Exception as e:
            logging.error(f'[games]\tCould not read check-ins: {e}')
            self.data = {}

    def save(self):
        with open(self.file_path, 'wb') as f:
            pickle.dump(self.data, f)


user_balance = UserBalance()
profit_and_loss = ProfitAndLoss()
check_in = CheckIn()


def settle_bet(user_id: int, stake: int | float, returned: int | float) -> Tuple[float, float]:
    """
    Pay a finished wager out and book what it made or cost.

    Every game ends here, and only here, so that the balance and the
    profit column can never disagree about what a hand was worth. The
    stake left the balance when the bet was placed, so only what comes
    back goes in; the profit is the difference between the two.
    """
    profit = fmt_balance(returned - stake)
    balance = user_balance.add_balance(user_id, returned) if returned \
        else user_balance.get_balance(user_id)
    profit_and_loss.record(user_id, profit)
    return balance, profit
