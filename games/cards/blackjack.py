from typing import List, Tuple
from games.cards.card import Card, Deck, generate_deck


BLACKJACK = 21
DEALER_STANDS_ON = 17


def get_blackjack_value(rank: str) -> int:
    """An ace counts eleven here; `hand_value` demotes it when it has to."""
    match rank:
        case 'A':
            return 11
        case 'J' | 'Q' | 'K':
            return 10
        case _:
            return int(rank)


class BlackjackCard(Card):
    def __init__(self, rank: str, suit: str):
        super().__init__(rank, suit)
        self.value = get_blackjack_value(self.rank)


class BlackjackDeck(Deck):
    def __init__(self, cards: List[BlackjackCard] = None, deck: Deck = None):
        super().__init__(cards)
        if deck:
            self.cards = [BlackjackCard(c.rank, c.suit) for c in deck.cards]


def gen_blackjack_deck(num: int = 6) -> BlackjackDeck:
    """Six decks, the way a real shoe is dealt."""
    return BlackjackDeck(deck=generate_deck() * num)


def hand_value(cards: List[Card]) -> Tuple[int, bool]:
    """
    The best total a hand can make, and whether an ace is still floating.

    Aces start at eleven and get demoted one at a time until the hand
    fits under twenty-one; a hand that still holds an eleven is "soft"
    and cannot go bust on the next card.
    """
    total = sum(c.value for c in cards)
    aces = sum(1 for c in cards if c.rank == 'A')
    while total > BLACKJACK and aces:
        total -= 10
        aces -= 1
    return total, bool(aces)


def is_blackjack(cards: List[Card]) -> bool:
    return len(cards) == 2 and hand_value(cards)[0] == BLACKJACK


def is_bust(cards: List[Card]) -> bool:
    return hand_value(cards)[0] > BLACKJACK


def dealer_should_draw(cards: List[Card]) -> bool:
    """The dealer has no choices: draw to seventeen, then stop."""
    total, _ = hand_value(cards)
    return total < DEALER_STANDS_ON


def show(cards: List[Card]) -> str:
    return ' '.join(str(c) for c in cards)


def settle(player: List[Card], dealer: List[Card]) -> Tuple[str, float]:
    """
    Who won, and what the stake comes back as a multiple of itself.

    Natural blackjack pays three to two; everything else is even money,
    and a tie hands the stake back.
    """
    player_total, _ = hand_value(player)
    dealer_total, _ = hand_value(dealer)

    if player_total > BLACKJACK:
        return '爆牌，庄家赢', 0
    if is_blackjack(player) and not is_blackjack(dealer):
        return '黑杰克！', 2.5
    if is_blackjack(dealer) and not is_blackjack(player):
        return '庄家黑杰克', 0
    if dealer_total > BLACKJACK:
        return '庄家爆牌，你赢了', 2.0
    if player_total > dealer_total:
        return '你赢了', 2.0
    if player_total < dealer_total:
        return '庄家赢', 0
    return '和局', 1.0
