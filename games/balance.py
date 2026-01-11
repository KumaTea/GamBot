import os
import pickle
from typing import Dict


BALANCE_DATA_DIR = 'data/games'
BALANCE_DATA_FILE = 'balance.p'
STARTING_BALANCE = 10000  # Initial money for new users
MINIMUM_BALANCE = 10  # 救济金起点
WELFARE_AMOUNT = 1000  # 救济金金额


def ensure_data_dir():
    """Ensure the data directory exists"""
    if not os.path.exists(BALANCE_DATA_DIR):
        os.makedirs(BALANCE_DATA_DIR, exist_ok=True)


def fmt_balance(amount: int | float) -> float:
    """Format balance to 2 decimal places"""
    return round(amount, 2)


class UserBalance:
    def __init__(self):
        self.balances: Dict[int, float] = {}  # user_id -> balance
        ensure_data_dir()
        self.load()

    def get_balance(self, user_id: int) -> float:
        """Get user's balance, initialize if new user"""
        if user_id not in self.balances:
            self.balances[user_id] = fmt_balance(STARTING_BALANCE)
            self.save()
        return self.balances[user_id]

    def set_balance(self, user_id: int, amount: int | float):
        """Set user's balance"""
        self.balances[user_id] = amount
        self.save()

    def add_balance(self, user_id: int, amount: int | float) -> float:
        """Add to user's balance and return new balance"""
        current = self.get_balance(user_id)
        new_balance = current + amount
        self.set_balance(user_id, new_balance)
        return new_balance

    def subtract_balance(self, user_id: int, amount: int | float) -> bool:
        """Subtract from user's balance. Returns True if successful, False if insufficient funds"""
        current = self.get_balance(user_id)
        if current < amount:
            return False
        new_balance = current - amount
        self.set_balance(user_id, new_balance)
        return True

    def load(self):
        """Load balances from file"""
        file_path = f'{BALANCE_DATA_DIR}/{BALANCE_DATA_FILE}'
        if os.path.isfile(file_path):
            try:
                with open(file_path, 'rb') as f:
                    self.balances = pickle.load(f)
            except Exception:
                self.balances = {}

    def save(self):
        """Save balances to file"""
        file_path = f'{BALANCE_DATA_DIR}/{BALANCE_DATA_FILE}'
        with open(file_path, 'wb') as f:
            pickle.dump(self.balances, f)


user_balance = UserBalance()
