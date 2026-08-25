from typing import List, Tuple
from bot.session import urandom


REELS = 3

# symbol, how often it comes up, what three of them pay
SYMBOLS: List[Tuple[str, int, float]] = [
    ('7️⃣', 1, 120),
    ('💎', 2, 40),
    ('🔔', 3, 18),
    ('🍉', 5, 9),
    ('🍋', 7, 5),
    ('🍒', 9, 3),
]

# a pair pays only for the two commonest symbols; between that and the
# table above the machine keeps about 4.4% over a long night (RTP 0.956,
# exact -- `python -m games.slots` re-checks it by simulation)
PAIR_PAYOUT = {'🍒': 2.0, '🍋': 1.4}

FACES = [s for s, _, _ in SYMBOLS]
WEIGHTS = [w for _, w, _ in SYMBOLS]
TRIPLE_PAYOUT = {s: p for s, _, p in SYMBOLS}

MIN_STAKE = 10
MAX_STAKE = 100000


def spin() -> List[str]:
    return urandom.choices(FACES, weights=WEIGHTS, k=REELS)


def payout_rate(reels: List[str]) -> Tuple[float, str]:
    """
    What a line pays, as a multiple of the stake, and what to call it.

    A rate of 0 means the stake is gone; 1 means it comes back.
    """
    first = reels[0]
    if all(r == first for r in reels):
        return TRIPLE_PAYOUT[first], f'三个 {first}'

    for face in set(reels):
        if reels.count(face) == 2 and face in PAIR_PAYOUT:
            return PAIR_PAYOUT[face], f'两个 {face}'

    return 0, '没中'


def rtp(trials: int = 200000) -> float:
    """Long-run return to player -- a sanity check, not used at runtime."""
    total = sum(payout_rate(spin())[0] for _ in range(trials))
    return total / trials


if __name__ == '__main__':
    print(f'{rtp():.4f}')
