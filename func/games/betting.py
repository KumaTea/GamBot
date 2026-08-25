import time
from typing import Dict, Optional
from dataclasses import dataclass, field


@dataclass
class Bet:
    bet_type: str
    amount: int


@dataclass
class Table:
    """
    One round of a betting game, from the first button to the payout.

    Everything the betting message needs to redraw itself lives here, so
    the countdown loop and the button handler render from the same place
    instead of editing each other's text.
    """
    chat_id: int
    opener: int
    header: str
    deadline: float
    msg_id: int = 0
    open: bool = True
    start_now: bool = False
    bets: Dict[int, Bet] = field(default_factory=dict)
    picks: Dict[int, Bet] = field(default_factory=dict)   # chosen, not yet confirmed
    result: Optional[dict] = None

    @property
    def seconds_left(self) -> int:
        return max(0, int(round(self.deadline - time.time())))


class BettingState:
    """The tables currently taking bets, by chat."""
    def __init__(self):
        self.tables: Dict[int, Table] = {}

    def start_betting(self, chat_id: int, opener: int, header: str, seconds: int) -> Table:
        table = Table(
            chat_id=chat_id,
            opener=opener,
            header=header,
            deadline=time.time() + seconds,
        )
        self.tables[chat_id] = table
        return table

    def get(self, chat_id: int) -> Optional[Table]:
        return self.tables.get(chat_id)

    def is_betting_open(self, chat_id: int) -> bool:
        table = self.tables.get(chat_id)
        return bool(table and table.open)

    def place_bet(self, chat_id: int, user_id: int, bet_type: str, amount: int) -> Optional[int]:
        """
        Take a confirmed bet.

        Returns what to hand back for a bet this player had already
        placed -- changing your mind used to silently keep the old
        stake -- or None when betting has closed.
        """
        table = self.tables.get(chat_id)
        if not table or not table.open:
            return None
        previous = table.bets.get(user_id)
        table.bets[user_id] = Bet(bet_type, amount)
        return previous.amount if previous else 0

    def undo_bet(self, chat_id: int, user_id: int) -> int:
        """Take a bet back off the table, returning the stake to refund."""
        table = self.tables.get(chat_id)
        if not table or not table.open:
            return 0
        bet = table.bets.pop(user_id, None)
        return bet.amount if bet else 0

    def get_bets(self, chat_id: int) -> Dict[int, Bet]:
        table = self.tables.get(chat_id)
        return table.bets if table else {}

    def pick(self, chat_id: int, user_id: int) -> Optional[Bet]:
        """A player's half-made selection, created empty on first touch."""
        table = self.tables.get(chat_id)
        if not table or not table.open:
            return None
        return table.picks.setdefault(user_id, Bet('', 0))

    def drop_pick(self, chat_id: int, user_id: int) -> bool:
        table = self.tables.get(chat_id)
        if not table:
            return False
        return table.picks.pop(user_id, None) is not None

    def close_betting(self, chat_id: int):
        table = self.tables.get(chat_id)
        if table:
            table.open = False
            table.picks.clear()

    def set_game_result(self, chat_id: int, **result):
        table = self.tables.get(chat_id)
        if table:
            table.result = result

    def clear_game(self, chat_id: int):
        self.tables.pop(chat_id, None)


betting_state = BettingState()
