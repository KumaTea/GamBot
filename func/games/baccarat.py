import asyncio
from typing import Optional
from telethon import Button
from bot.session import urandom
from common.data import BACCARAT_RULE
from telethon.tl.custom import Message
from games.balance import money, user_balance
from games.cards.card import generate_deck
from func.games.betting import Table, betting_state
from func.games.wallet import bettor_name
from func.games.share import busy_notice, edit_text, game_status, table
from games.cards.baccarat import BaccaratDeck, banker_should_draw, player_should_draw


GAME_NAME = '百家乐'
BET_NAMES = {'player': '闲家', 'banker': '庄家', 'tie': '和局'}
BET_ODDS = {'player': '1:1', 'banker': '0.95:1', 'tie': '8:1'}
# what a winning stake comes back as, itself included
PAYOUT = {'player': 2.0, 'banker': 1.95, 'tie': 9.0}
ODDS_LINE = '　'.join(f'{BET_NAMES[k]} {o}' for k, o in BET_ODDS.items())

BETTING_SECONDS = 60
TICK_SECONDS = 5
DEAL_PAUSE = 2
MIN_BET = 10
MAX_BET = 1000000
SHOE_DECKS = 8
SHOE_LOW_WATER = 20          # a hand can want six cards; reshuffle well before that
CLEANUP_AFTER = 10 * 60      # when the transcript is folded back up

CHIPS = [100, 500, 1000, 5000]


class GameTable:
    """The shoe each chat is dealing out of."""
    def __init__(self):
        self.groups = {}


game_table = GameTable()


def gen_baccarat_deck(num: int = SHOE_DECKS) -> BaccaratDeck:
    return BaccaratDeck(deck=generate_deck() * num)


def betting_buttons(chat_id: int) -> list:
    def data(action: str, value) -> bytes:
        return f'bac:{chat_id}:{action}:{value}'.encode()

    return [
        [Button.inline(f'{BET_NAMES[key]} {odds}', data('type', key))
         for key, odds in BET_ODDS.items()],
        [Button.inline(f'+{chip}', data('amt', chip)) for chip in CHIPS],
        [
            Button.inline('梭哈', data('amt', 'all')),
            Button.inline('取消', data('no', 0)),
            Button.inline('下注', data('ok', 0)),
            Button.inline('开牌', data('go', 0)),
        ],
    ]


async def render_betting(state: Table, client) -> str:
    """
    The whole betting message, from scratch.

    Both the countdown and the buttons call this, so there is only ever
    one idea of what the message should say.
    """
    text = state.header
    text += f'\n现在是下注时间，还有 **{state.seconds_left}** 秒。\n'
    text += f'{ODDS_LINE}\n\n'
    text += '**当前下注：**\n'
    text += await format_bets(state, client)
    return text


async def format_bets(state: Table, client) -> str:
    if not state.bets:
        return '暂无下注\n'
    lines = []
    for user_id, bet in state.bets.items():
        name = await bettor_name(client, user_id)
        lines.append(f'• {name}：{BET_NAMES[bet.bet_type]} {money(bet.amount)}')
    return '\n'.join(lines) + '\n'


async def take_bets(event, state: Table) -> Message:
    """Run the betting window, redrawing the countdown as it goes."""
    client = event.client
    reply = await event.respond(
        await render_betting(state, client),
        buttons=betting_buttons(event.chat_id)
    )
    state.msg_id = reply.id
    game_status.set_message(event.chat_id, reply.id)

    while state.seconds_left > 0 and not state.start_now:
        await asyncio.sleep(min(TICK_SECONDS, max(1, state.seconds_left)))
        if state.start_now:
            break
        reply = await edit_text(
            reply,
            await render_betting(state, client),
            betting_buttons(event.chat_id)
        )
    return reply


async def deal_hand(deck: BaccaratDeck):
    """
    Play out one hand and return the running commentary.

    第一及第三张牌发给闲家，第二及第四张牌则发给庄家。
    """
    player = [deck.deal()]
    banker = [deck.deal()]
    player.append(deck.deal())
    banker.append(deck.deal())

    player_value = points(player)
    banker_value = points(banker)

    steps = [
        f'闲家：{player[0]} {player[1]}，{player_value} 点。\n'
        f'庄家：{banker[0]} {banker[1]}，{banker_value} 点。\n'
    ]

    if player_value >= 8 or banker_value >= 8:
        steps.append(f'有一家例牌，双方[不需要补牌]({BACCARAT_RULE})！\n')
    else:
        player_drew = player_should_draw(player_value)
        drawn_value = 0
        if player_drew:
            card = deck.deal()
            player.append(card)
            drawn_value = card.value
            player_value = points(player)
            steps.append(f'闲家[补牌]({BACCARAT_RULE}) {card}，{player_value} 点。\n')
        else:
            steps.append(f'闲家[不需要补牌]({BACCARAT_RULE})。\n')

        if banker_should_draw(player_drew, drawn_value, banker_value):
            card = deck.deal()
            banker.append(card)
            banker_value = points(banker)
            steps.append(f'庄家[补牌]({BACCARAT_RULE}) {card}，{banker_value} 点。\n')
        else:
            steps.append(f'庄家[不需要补牌]({BACCARAT_RULE})。\n')

    if player_value > banker_value:
        result, result_text = 'player', '闲家获胜'
    elif player_value < banker_value:
        result, result_text = 'banker', '庄家获胜'
    else:
        result, result_text = 'tie', '和局'

    return steps, result, f'{result_text}（闲 {player_value} : {banker_value} 庄）'


def points(cards) -> int:
    """Baccarat counts modulo ten."""
    return sum(c.value for c in cards) % 10


async def prepare_shoe(chat_id: int, reply: Message, text: str) -> tuple:
    deck = game_table.groups.get(chat_id)
    if deck is not None and len(deck) >= SHOE_LOW_WATER:
        return deck, text, reply

    deck = gen_baccarat_deck()
    shuffles = urandom.randint(1, 10)
    for _ in range(shuffles):
        deck.shuffle()
    game_table.groups[chat_id] = deck

    text += f'\n发牌箱空了。荷官拿了 {SHOE_DECKS} 副牌，洗了 {shuffles} 次。\n'
    reply = await edit_text(reply, text)
    await asyncio.sleep(DEAL_PAUSE)
    return deck, text, reply


async def settle(state: Table, client, result: str) -> str:
    if not state.bets:
        return ''
    lines = ['**结算：**']
    for user_id, bet in state.bets.items():
        name = await bettor_name(client, user_id)
        bet_name = BET_NAMES[bet.bet_type]
        if bet.bet_type == result:
            winnings = int(bet.amount * PAYOUT[result])
            balance = user_balance.add_balance(user_id, winnings)
            profit = winnings - bet.amount
            lines.append(
                f'✓ {name}：{bet_name} {money(bet.amount)} → +{money(profit)}'
                f'（余额 {money(balance)}）')
        else:
            balance = user_balance.get_balance(user_id)
            lines.append(
                f'✗ {name}：{bet_name} {money(bet.amount)} → -{money(bet.amount)}'
                f'（余额 {money(balance)}）')
    return '\n'.join(lines) + '\n'


def fold_up_later(reply: Message, summary: str):
    """
    Replace the play-by-play with a one-line summary, later.

    The transcript is the fun part while it is happening and clutter
    half an hour afterwards -- but the handler must not sit here for ten
    minutes holding the chat's table, so this goes off on its own.
    """
    async def cleanup():
        await asyncio.sleep(CLEANUP_AFTER)
        await edit_text(reply, summary)

    asyncio.create_task(cleanup())


async def start_baccarat(event) -> Optional[Message]:
    busy = await busy_notice(event)
    if busy:
        return await event.respond(busy, link_preview=False)

    user = await event.get_sender()
    if not user:
        return None

    async with table(event, GAME_NAME):
        chat_id = event.chat_id
        client = event.client
        header = f'{await bettor_name(client, user.id)} 开了一局{GAME_NAME}！\n'

        state = betting_state.start_betting(chat_id, user.id, header, BETTING_SECONDS)
        try:
            reply = await take_bets(event, state)

            betting_state.close_betting(chat_id)
            text = header + '\n下注截止。\n' + await format_bets(state, client)
            reply = await edit_text(reply, text, buttons=None)
            await asyncio.sleep(DEAL_PAUSE)

            deck, text, reply = await prepare_shoe(chat_id, reply, text)

            steps, result, result_text = await deal_hand(deck)
            for step in steps:
                text += step
                reply = await edit_text(reply, text)
                await asyncio.sleep(DEAL_PAUSE)

            headline = f'结果：**{result_text}**'
            text += f'\n{headline}\n'
            reply = await edit_text(reply, text)
            await asyncio.sleep(DEAL_PAUSE)

            settlement = await settle(state, client, result)
            if settlement:
                text += '\n' + settlement
            text += '\n/baccarat 再来一局！'
            reply = await edit_text(reply, text)
        finally:
            betting_state.clear_game(chat_id)

    summary = f'{GAME_NAME} /baccarat\n{headline}\n'
    if settlement:
        summary += '\n' + settlement
    fold_up_later(reply, summary)
    return reply
