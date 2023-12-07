from typing import List
from games.cards.card import Card, Deck


def get_baccarat_value(rank: str) -> int:
    match rank:
        case 'A':
            return 1
        case 'J' | 'Q' | 'K' | '10':
            return 0
        case _:
            return int(rank)


class BaccaratCard(Card):
    def __init__(self, rank: str, suit: str):
        super().__init__(rank, suit)
        self.value = get_baccarat_value(self.rank)


class BaccaratDeck(Deck):
    def __init__(self, cards: List[BaccaratCard] = None, deck: Deck = None):
        super().__init__(cards)
        if deck:
            self.cards = deck.cards
            self.cards_to_baccarat_cards()

    def cards_to_baccarat_cards(self):
        self.cards = [BaccaratCard(card.rank, card.suit) for card in self.cards]


def player_should_draw(player_value: int) -> bool:
    if player_value <= 5:
        return True
    return False


def banker_should_draw(
        player_has_drawn: bool,
        player_drawn_value: int,
        banker_value: int
) -> bool:
    if not player_has_drawn:
        return player_should_draw(banker_value)

    if banker_value <= 2:
        return True
    elif banker_value == 3 and player_drawn_value != 8:
        return True
    elif banker_value == 4 and player_drawn_value in [2, 3, 4, 5, 6, 7]:
        return True
    elif banker_value == 5 and player_drawn_value in [4, 5, 6, 7]:
        return True
    elif banker_value == 6 and player_drawn_value in [6, 7]:
        return True
    return False
