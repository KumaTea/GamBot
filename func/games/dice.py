import asyncio
from typing import Optional, Tuple
from share.auth import ensure_auth
from func.games.share import edit_text
from telethon.tl.custom import Message
from games.balance import money, user_balance
from func.games.wallet import bettor_name, take_stake
from games.dice import (
    BET_NAMES, MAX_STAKE, MIN_STAKE, PAYOUT,
    faces, outcome, parse_bet, roll, wins
)


GAME_NAME = '骰宝'
USAGE = (
    '用法：/dice 大 100\n'
    '可押 **大**（11-17）、**小**（4-10）、**豹子**（三个一样，30:1）。\n'
    '豹子通吃大小。'
)
ROLL_PAUSE = 1.5


def read_args(args: list) -> Tuple[str, str]:
    """
    Pull the bet and the stake out, in whichever order they were typed.

    `/dice 大 100` and `/dice 100 大` mean the same thing to a person, so
    they should mean the same thing here.
    """
    bet, stake = '', ''
    for word in args[:2]:
        found = parse_bet(word)
        if found and not bet:
            bet = found
        elif not stake:
            stake = word
    return bet, stake


@ensure_auth
async def command_dice(event) -> Optional[Message]:
    args = (event.raw_text or '').split()[1:]
    bet, stake_word = read_args(args)
    if not bet:
        return await event.respond(USAGE)

    stake, complaint = await take_stake(event, stake_word, MIN_STAKE, MAX_STAKE)
    if complaint:
        return complaint

    name = await bettor_name(event.client, event.sender_id)
    header = f'**{GAME_NAME}** — {name}\n押 {BET_NAMES[bet]} {money(stake)}\n\n'

    message = await event.respond(header + '　骰盅摇起来了…')
    await asyncio.sleep(ROLL_PAUSE)

    dice = roll()
    _, said = outcome(dice)
    text = header + f'　{faces(dice)}\n　**{said}**\n'
    message = await edit_text(message, text)

    won = wins(bet, dice)
    returned = int(stake * PAYOUT[bet]) if won else 0
    balance = user_balance.add_balance(event.sender_id, returned) if returned \
        else user_balance.get_balance(event.sender_id)
    profit = returned - stake
    sign = '+' if profit > 0 else ''

    text += (
        f'\n{"中了！" if won else "没中。"}\n'
        f'{sign}{money(profit)}（余额 {money(balance)}）\n'
        f'\n/dice 再来一把！'
    )
    await asyncio.sleep(ROLL_PAUSE)
    return await edit_text(message, text)
