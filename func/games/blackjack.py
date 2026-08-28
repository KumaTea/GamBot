import asyncio
import logging
from itertools import count
from typing import Dict, Optional
from telethon import Button
from dataclasses import dataclass, field
from telethon.tl.custom import Message
from share.auth import ensure_auth
from func.games.turns import in_turn
from func.fading import transient
from func.games.share import edit_text
from games.balance import money, settle_bet, signed, user_balance
from func.games.wallet import bettor_name, take_stake
from games.cards.blackjack import (
    BlackjackDeck, gen_blackjack_deck, hand_value,
    dealer_should_draw, is_blackjack, is_bust, settle, show
)


GAME_NAME = '21点'
MIN_BET = 10
MAX_BET = 1000000
ABANDON_AFTER = 5 * 60   # an untouched hand plays itself out
DEAL_PAUSE = 1.2


@dataclass
class Hand:
    """One player against the dealer, for the length of one hand."""
    chat_id: int
    user_id: int
    name: str
    stake: int
    deck: BlackjackDeck
    player: list = field(default_factory=list)
    dealer: list = field(default_factory=list)
    doubled: bool = False
    over: bool = False
    watchdog: Optional[asyncio.Task] = None
    # set the moment the hand is settled, however it ended -- what the
    # command waits on so a player's next hand does not start on top
    done: asyncio.Event = field(default_factory=asyncio.Event)


hands: Dict[int, Hand] = {}
# hands are keyed by a number of their own rather than by the message
# they sit on, so the buttons can be built before the message exists
next_hand_id = count(1).__next__


def action_buttons(hand_id: int, hand: Hand) -> list:
    def data(action: str) -> bytes:
        return f'bj:{hand_id}:{action}'.encode()

    row = [Button.inline('要牌', data('hit')), Button.inline('停牌', data('stand'))]
    # doubling is only ever offered on the opening two cards
    if len(hand.player) == 2 and not hand.doubled:
        row.append(Button.inline('双倍', data('double')))
    return [row]


def render(hand: Hand, hide_dealer: bool = True, tail: str = '') -> str:
    player_total, soft = hand_value(hand.player)
    player_line = f'你：{show(hand.player)} — **{player_total}**{" 软" if soft else ""} 点'

    if hide_dealer:
        dealer_line = f'庄家：{hand.dealer[0]} 🂠'
    else:
        dealer_total, _ = hand_value(hand.dealer)
        dealer_line = f'庄家：{show(hand.dealer)} — **{dealer_total}** 点'

    text = (
        f'**{GAME_NAME}** — {hand.name}\n'
        f'注额 {money(hand.stake)}\n\n'
        f'{dealer_line}\n'
        f'{player_line}\n'
    )
    return text + tail


def finish(hand: Hand) -> str:
    """Pay the hand out and describe what happened."""
    verdict, rate = settle(hand.player, hand.dealer)
    returned = int(hand.stake * rate)
    # `hand.stake` is already the doubled figure where it was doubled,
    # and both halves of it have been taken, so this is the whole wager
    balance, profit = settle_bet(hand.user_id, hand.stake, returned)

    return (
        f'\n**{verdict}**\n'
        f'{signed(profit)}（余额 {money(balance)}）\n'
        f'\n/blackjack 再来一局！'
    )


async def play_dealer(message: Message, hand: Hand) -> Message:
    """The dealer turns over and draws to seventeen."""
    message = await edit_text(message, render(hand, hide_dealer=False), buttons=None)
    await asyncio.sleep(DEAL_PAUSE)

    while dealer_should_draw(hand.dealer):
        hand.dealer.append(hand.deck.deal())
        message = await edit_text(message, render(hand, hide_dealer=False))
        await asyncio.sleep(DEAL_PAUSE)

    message = await edit_text(message, render(hand, hide_dealer=False, tail=finish(hand)))
    hand.done.set()
    return message


def close(hand_id: int):
    hand = hands.pop(hand_id, None)
    if hand and hand.watchdog:
        hand.watchdog.cancel()


def watch(hand_id: int, message: Message, hand: Hand):
    """
    A hand nobody comes back to still has to end.

    The stake is already off the player, so an abandoned game would
    otherwise just swallow it.
    """
    async def timeout():
        await asyncio.sleep(ABANDON_AFTER)
        if hand.over:
            return
        hand.over = True
        logging.info(f'[games]\tBlackjack hand {hand_id} abandoned, standing for them')
        hands.pop(hand_id, None)
        await play_dealer(message, hand)

    hand.watchdog = asyncio.create_task(timeout())


@ensure_auth
@transient
@in_turn
async def command_blackjack(event) -> Optional[Message]:
    args = (event.raw_text or '').split()[1:]
    stake, complaint = await take_stake(event, args[0] if args else '', MIN_BET, MAX_BET)
    if complaint:
        return complaint

    deck = gen_blackjack_deck()
    deck.shuffle()
    hand = Hand(
        chat_id=event.chat_id,
        user_id=event.sender_id,
        name=await bettor_name(event.client, event.sender_id),
        stake=stake,
        deck=deck,
    )
    hand.player = [deck.deal(), deck.deal()]
    hand.dealer = [deck.deal(), deck.deal()]

    # a natural on either side ends it before anyone gets a choice
    if is_blackjack(hand.player) or is_blackjack(hand.dealer):
        hand.over = True
        message = await event.respond(render(hand, hide_dealer=False))
        return await edit_text(message, render(hand, hide_dealer=False, tail=finish(hand)))

    hand_id = next_hand_id()
    hands[hand_id] = hand
    message = await event.respond(render(hand), buttons=action_buttons(hand_id, hand))
    watch(hand_id, message, hand)

    # the seat is held until the hand is actually over, buttons and all.
    # The watchdog above guarantees that happens; the wait is bounded
    # anyway, because a seat held by a hand that somehow never ended
    # would lock the player out of the casino for good.
    try:
        await asyncio.wait_for(hand.done.wait(), ABANDON_AFTER + 60)
    except asyncio.TimeoutError:
        logging.warning(f'[games]\tBlackjack hand {hand_id} never settled')
    return message


async def handle_action(event, hand_id: int, action: str) -> None:
    """One button press on a hand in progress."""
    hand = hands.get(hand_id)
    if not hand or hand.over:
        return await event.answer('这局已经结束了。', alert=True)
    if event.sender_id != hand.user_id:
        return await event.answer('这是别人的牌。', alert=True)

    message = await event.get_message()

    if action == 'double':
        if len(hand.player) != 2 or hand.doubled:
            return await event.answer('现在不能加倍。')
        if not user_balance.subtract_balance(hand.user_id, hand.stake):
            return await event.answer(
                f'余额不足，你只有 {money(user_balance.get_balance(hand.user_id))}。',
                alert=True)
        hand.doubled = True
        hand.stake *= 2
        hand.player.append(hand.deck.deal())
        await event.answer(f'加倍到 {money(hand.stake)}')
        hand.over = True
        close(hand_id)
        if is_bust(hand.player):
            await edit_text(message, render(hand, hide_dealer=False, tail=finish(hand)), None)
            hand.done.set()
        else:
            await play_dealer(message, hand)
        return None

    if action == 'hit':
        hand.player.append(hand.deck.deal())
        total, _ = hand_value(hand.player)
        await event.answer(f'{hand.player[-1]}，{total} 点')
        if is_bust(hand.player):
            hand.over = True
            close(hand_id)
            await edit_text(message, render(hand, hide_dealer=False, tail=finish(hand)), None)
            hand.done.set()
        else:
            await edit_text(message, render(hand), action_buttons(hand_id, hand))
        return None

    if action == 'stand':
        hand.over = True
        close(hand_id)
        await event.answer('停牌')
        await play_dealer(message, hand)
    return None
