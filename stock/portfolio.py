import os
import pickle
import logging
from typing import Dict, Optional
from dataclasses import dataclass
from common.data import STOCK_DATA_DIR, STOCK_PORTFOLIO_FILE


LOT_SIZE = 100          # A shares deal in hundreds
COMMISSION_RATE = 0.00025
COMMISSION_MIN = 5.0
STAMP_DUTY_RATE = 0.0005    # sellers only
TRANSFER_FEE_RATE = 0.00001

STORE_FILE = f'{STOCK_DATA_DIR}/{STOCK_PORTFOLIO_FILE}'


@dataclass
class Holding:
    shares: int = 0
    cost: float = 0.0   # everything paid to get here, fees included

    @property
    def average(self) -> float:
        return self.cost / self.shares if self.shares else 0.0


def buy_fees(gross: float) -> float:
    """Commission and the transfer fee, the way a broker charges them."""
    commission = max(gross * COMMISSION_RATE, COMMISSION_MIN)
    return round(commission + gross * TRANSFER_FEE_RATE, 2)


def sell_fees(gross: float) -> float:
    """The same, plus the stamp duty that only sellers pay."""
    commission = max(gross * COMMISSION_RATE, COMMISSION_MIN)
    duty = gross * STAMP_DUTY_RATE
    return round(commission + duty + gross * TRANSFER_FEE_RATE, 2)


@dataclass
class Trade:
    code: str
    shares: int
    price: float
    gross: float
    fees: float
    cash: float               # what leaves (buy) or arrives (sell)
    profit: Optional[float] = None   # realised, on a sell


class Portfolio:
    """
    Who holds what, at what cost.

    Positions only -- the money itself lives in the same balance the
    card games use, so a bad week at the table shows up in the trading
    account and the other way round.
    """
    def __init__(self, file: str = STORE_FILE):
        self.file = file
        self.data: Dict[int, Dict[str, Holding]] = {}
        os.makedirs(STOCK_DATA_DIR, exist_ok=True)
        self.load()

    def holdings(self, user_id: int) -> Dict[str, Holding]:
        return self.data.get(user_id, {})

    def holding(self, user_id: int, code: str) -> Holding:
        return self.holdings(user_id).get(code, Holding())

    def quote_buy(self, code: str, shares: int, price: float) -> Trade:
        gross = round(shares * price, 2)
        fees = buy_fees(gross)
        return Trade(code, shares, price, gross, fees, round(gross + fees, 2))

    def quote_sell(self, user_id: int, code: str, shares: int, price: float) -> Trade:
        gross = round(shares * price, 2)
        fees = sell_fees(gross)
        net = round(gross - fees, 2)
        held = self.holding(user_id, code)
        basis = held.average * shares
        return Trade(code, shares, price, gross, fees, net, round(net - basis, 2))

    def apply_buy(self, user_id: int, trade: Trade):
        book = self.data.setdefault(user_id, {})
        held = book.setdefault(trade.code, Holding())
        held.shares += trade.shares
        held.cost = round(held.cost + trade.cash, 2)
        self.save()

    def apply_sell(self, user_id: int, trade: Trade):
        book = self.data.setdefault(user_id, {})
        held = book.get(trade.code)
        if not held:
            return
        # the cost basis leaves in the same proportion as the shares
        basis = held.average * trade.shares
        held.shares -= trade.shares
        held.cost = round(max(0.0, held.cost - basis), 2)
        if held.shares <= 0:
            del book[trade.code]
        if not book:
            del self.data[user_id]
        self.save()

    def load(self):
        if not os.path.isfile(self.file):
            return
        try:
            with open(self.file, 'rb') as f:
                self.data = pickle.load(f)
        except Exception as e:
            logging.error(f'[stock]\tCould not read portfolios: {e}')
            self.data = {}

    def save(self):
        with open(self.file, 'wb') as f:
            pickle.dump(self.data, f)


portfolio = Portfolio()
