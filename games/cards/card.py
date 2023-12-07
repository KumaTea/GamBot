import random
from typing import List, Union
from games.cards.data import CARD_SYMBOLS


# from __future__ import annotations
# use typing.Self
try:
    from typing import Self
except ImportError:
    from typing_extensions import Self


def get_card_rank(rank: Union[int, str]) -> str:
    if isinstance(rank, int):
        if rank == 1:
            return 'A'
        elif rank == 11:
            return 'J'
        elif rank == 12:
            return 'Q'
        elif rank == 13:
            return 'K'
        else:
            return str(rank)
    elif isinstance(rank, str):
        if rank.upper() in ['J', 'Q', 'K', 'A']:
            return rank.upper()
        elif rank.isdigit():
            return rank
        else:
            raise ValueError('Invalid card rank')
    else:
        raise TypeError('Invalid card rank')


def suit_to_symbol(suit: str) -> str:
    if suit == 'S':
        return '♠'
    elif suit == 'H':
        return '♥'
    elif suit == 'D':
        return '♦'
    elif suit == 'C':
        return '♣'
    else:
        return suit


def get_card_value(rank: str) -> int:
    match rank:
        case 'A':
            return 1
        case 'J':
            return 11
        case 'Q':
            return 12
        case 'K':
            return 13
        case _:
            return int(rank)


class Card:
    def __init__(self, rank: str, suit: str = '🂠', value: int = 0, face_up: bool = True):
        self.rank = get_card_rank(rank)
        self.suit = suit
        if value:
            self.value = value
        else:
            self.value = get_card_value(self.rank)
        self.face_up = face_up

    def __str__(self):
        return f'{suit_to_symbol(self.suit)}{self.rank}'

    def __repr__(self):
        return f'{suit_to_symbol(self.suit)}{self.rank}'

    def __eq__(self, other):
        return self.value == other.value

    def __lt__(self, other):
        return self.value < other.value

    def __gt__(self, other):
        return self.value > other.value

    def flip(self):
        self.face_up = not self.face_up

    def symbol(self):
        if self.suit in CARD_SYMBOLS:
            return CARD_SYMBOLS[self.suit][self.rank]
        else:
            return CARD_SYMBOLS['S'][self.rank]


class Deck:
    def __init__(self, cards: List[Card] = None):
        if cards:
            self.cards = cards
        else:
            self.cards = []

    def shuffle(self) -> None:
        random.shuffle(self.cards)

    def deal(self) -> Card:
        return self.cards.pop(0)

    def add(self, card: Union[Card, List[Card]]):
        if isinstance(card, Card):
            self.cards.append(card)
        elif isinstance(card, list):
            self.cards.extend(card)
        else:
            raise TypeError('Must be a Card or list of Cards')

    def __add__(self, other: Self) -> Self:
        temp = Deck(self.cards.copy())
        temp.cards.extend(other.cards)
        return temp

    def __mul__(self, other: int) -> Self:
        temp = Deck()
        for _ in range(other):
            temp += self
        return temp

    def __len__(self):
        return len(self.cards)

    def copy(self) -> Self:
        return Deck(self.cards.copy())


def generate_deck() -> Deck:
    deck = Deck()
    for suit in ['S', 'H', 'D', 'C']:
        for rank in ['A', '2', '3', '4', '5', '6', '7',
                     '8', '9', '10', 'J', 'Q', 'K']:
            deck.add(Card(rank, suit))
    return deck
