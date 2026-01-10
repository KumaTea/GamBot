import os
import pickle
from typing import Dict


BALANCE_DATA_DIR = 'data/games'
BALANCE_DATA_FILE = 'balance.p'
STARTING_BALANCE = 1000  # Initial money for new users


def ensure_data_dir():
    """Ensure the data directory exists"""
    if not os.path.exists(BALANCE_DATA_DIR):
        os.makedirs(BALANCE_DATA_DIR, exist_ok=True)


class UserBalance:
    def __init__(self):
        self.balances: Dict[int, int] = {}  # user_id -> balance
        ensure_data_dir()
        self.load()

    def get_balance(self, user_id: int) -> int:
        """Get user's balance, initialize if new user"""
        if user_id not in self.balances:
            self.balances[user_id] = STARTING_BALANCE
            self.save()
        return self.balances[user_id]

    def set_balance(self, user_id: int, amount: int):
        """Set user's balance"""
        self.balances[user_id] = amount
        self.save()

    def add_balance(self, user_id: int, amount: int) -> int:
        """Add to user's balance and return new balance"""
        current = self.get_balance(user_id)
        new_balance = current + amount
        self.set_balance(user_id, new_balance)
        return new_balance

    def subtract_balance(self, user_id: int, amount: int) -> bool:
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
