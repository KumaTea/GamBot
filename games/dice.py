from typing import List, Tuple
from bot.session import urandom


DICE_FACES = {1: '⚀', 2: '⚁', 3: '⚂', 4: '⚃', 5: '⚄', 6: '⚅'}

BIG = 'big'
SMALL = 'small'
TRIPLE = 'triple'

BET_NAMES = {BIG: '大', SMALL: '小', TRIPLE: '豹子'}
BET_ALIASES = {
    '大': BIG, 'big': BIG, 'b': BIG,
    '小': SMALL, 'small': SMALL, 's': SMALL,
    '豹子': TRIPLE, '围骰': TRIPLE, 'triple': TRIPLE, 't': TRIPLE,
}

# 大/小 are even money and lose to a triple, so the house keeps 2.8%.
# Any triple pays 30:1 against odds of 1 in 36 -- 14% to the house, the
# price of the only bet on the table that pays real money.
PAYOUT = {BIG: 2.0, SMALL: 2.0, TRIPLE: 31.0}

MIN_STAKE = 10
MAX_STAKE = 100000


def parse_bet(word: str) -> str:
    return BET_ALIASES.get((word or '').strip().lower(), '')


def roll() -> List[int]:
    return [urandom.randint(1, 6) for _ in range(3)]


def faces(dice: List[int]) -> str:
    return ' '.join(DICE_FACES[d] for d in dice)


def is_triple(dice: List[int]) -> bool:
    return dice[0] == dice[1] == dice[2]


def outcome(dice: List[int]) -> Tuple[str, str]:
    """What the roll came to, and how to say it."""
    total = sum(dice)
    if is_triple(dice):
        return TRIPLE, f'豹子 {dice[0]}（{total} 点）'
    if total >= 11:
        return BIG, f'大（{total} 点）'
    return SMALL, f'小（{total} 点）'


def wins(bet: str, dice: List[int]) -> bool:
    """A triple takes 大 and 小 alike -- that is the whole house edge."""
    if bet == TRIPLE:
        return is_triple(dice)
    if is_triple(dice):
        return False
    total = sum(dice)
    return total >= 11 if bet == BIG else total <= 10
