import asyncio
import logging
from typing import Dict
from contextlib import asynccontextmanager


# how many games one player may have in flight at once, the one being
# played included -- past that the queue is the problem, not the wait
MAX_GAMES = 4

TOO_MANY = '你已经有几局在排队了，等这几局结束再来。'


class PlayerQueue:
    """
    One game at a time per player, in the order they asked for them.

    Five `/blackjack` fired off in a row are five games, not one. Played
    at the same time they interleave: each takes its stake, sleeps
    through its own dealing, and settles against whatever the balance
    had become by then, so the four that finish first are quietly
    overwritten by the one that finishes last. Played one after another
    each reads a balance the one before it has finished writing, which
    is the only ordering that can be totalled.

    A seat is held for as long as the game lasts, and a hand waiting on
    a button lasts until the player answers or the table gives up on
    them -- there is no such thing as playing two hands at once anyway.
    """
    def __init__(self, limit: int = MAX_GAMES):
        self.limit = limit
        self.seats: Dict[int, asyncio.Lock] = {}
        self.queued: Dict[int, int] = {}

    def waiting(self, user_id: int) -> int:
        """Games this player has in flight, the one being played included."""
        return self.queued.get(user_id, 0)

    def full(self, user_id: int) -> bool:
        return self.waiting(user_id) >= self.limit

    @asynccontextmanager
    async def turn(self, user_id: int):
        """Hold this player's seat for the length of one game."""
        seat = self.seats.setdefault(user_id, asyncio.Lock())
        self.queued[user_id] = self.waiting(user_id) + 1
        try:
            async with seat:
                yield
        finally:
            left = self.waiting(user_id) - 1
            if left > 0:
                self.queued[user_id] = left
            else:
                # the count is raised before the seat is taken and
                # lowered after it is given back, so nought here means
                # nobody else is holding this lock and it can go
                self.queued.pop(user_id, None)
                self.seats.pop(user_id, None)


player_queue = PlayerQueue()


def in_turn(func):
    """
    Wrap a single-player game so a player's games run one at a time.

    Baccarat is left out on purpose: the whole group plays one hand
    together, and the chat already holds a table of its own.
    """
    async def wrapper(event):
        user_id = event.sender_id
        if not user_id:
            return await func(event)
        if player_queue.full(user_id):
            logging.info(f'[games]\tUser {user_id} has {player_queue.waiting(user_id)} queued')
            return await event.respond(TOO_MANY)
        async with player_queue.turn(user_id):
            return await func(event)
    return wrapper
