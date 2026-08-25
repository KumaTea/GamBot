import logging
from typing import Optional, Tuple
from share.auth import ensure_auth
from telethon.tl.custom import Message
from share.common import get_user_name, mention_id
from games.balance import MINIMUM_BALANCE, WELFARE_AMOUNT, check_in, money, user_balance


ALL_IN_WORDS = {'all', 'allin', 'all-in', '梭哈', '全部', '全押', '梭'}
DEFAULT_STAKE = 100


def parse_stake(word: str, balance: float, minimum: int, maximum: int) -> Tuple[int, str]:
    """
    Read a stake off the command line.

    Returns (amount, complaint). A complaint means the amount is not
    usable and should be shown to the player instead of a game.
    """
    word = (word or '').strip().lower()
    if not word:
        amount = min(DEFAULT_STAKE, balance)
    elif word in ALL_IN_WORDS:
        amount = min(balance, maximum)
    else:
        try:
            amount = float(word)
        except ValueError:
            return 0, f'看不懂「{word}」是多少钱。'

    amount = int(amount)
    if amount < minimum:
        return 0, f'最少下注 {money(minimum)}。'
    if amount > maximum:
        return 0, f'最多下注 {money(maximum)}。'
    if amount > balance:
        return 0, f'余额不足，你只有 {money(balance)}。'
    return amount, ''


async def take_stake(event, word: str, minimum: int, maximum: int) -> Tuple[int, Optional[Message]]:
    """
    Parse a stake and take it off the player, in one step.

    Returns (amount, complaint). One of the two is always falsy: either
    the money is in the pot, or nothing at all has happened.
    """
    user_id = event.sender_id
    balance = user_balance.get_balance(user_id)
    amount, problem = parse_stake(word, balance, minimum, maximum)
    if problem:
        return 0, await event.respond(problem)
    if not user_balance.subtract_balance(user_id, amount):
        return 0, await event.respond(f'余额不足，你只有 {money(balance)}。')
    return amount, None


async def bettor_name(client, user_id: int) -> str:
    try:
        return get_user_name(await client.get_entity(user_id))
    except Exception:
        return f'用户{user_id}'


async def bettor_mention(client, user_id: int) -> str:
    return mention_id(user_id, await bettor_name(client, user_id))


@ensure_auth
async def command_balance(event) -> Message:
    user = await event.get_sender()
    if not user:
        return await event.respond('无法获取用户信息')

    balance = user_balance.get_balance(user.id)
    rank = user_balance.rank_of(user.id)
    return await event.respond(
        f'{get_user_name(user)} 的余额：**{money(balance)}**\n'
        f'排名：第 {rank} / {len(user_balance.balances)} 位'
    )


@ensure_auth
async def command_rank(event) -> Message:
    top = user_balance.top(10)
    if not top:
        return await event.respond('还没有人玩过。')

    medals = {1: '🥇', 2: '🥈', 3: '🥉'}
    lines = ['**富豪榜**']
    for place, (user_id, balance) in enumerate(top, start=1):
        marker = medals.get(place, f'{place}.')
        name = await bettor_name(event.client, user_id)
        lines.append(f'{marker} {name} — {money(balance)}')
    return await event.respond('\n'.join(lines))


@ensure_auth
async def command_checkin(event) -> Message:
    user_id = event.sender_id
    claimed, streak, amount = check_in.claim(user_id)
    if not claimed:
        return await event.respond(
            f'今天已经签到过了，已连续 {streak} 天。\n'
            f'当前余额：**{money(user_balance.get_balance(user_id))}**'
        )
    balance = user_balance.add_balance(user_id, amount)
    return await event.respond(
        f'签到成功，连续 {streak} 天，领到 **{money(amount)}**。\n'
        f'当前余额：**{money(balance)}**'
    )


@ensure_auth
async def command_give(event) -> Message:
    """Transfer money: reply to someone with /give 500, or /give <id> 500."""
    args = (event.raw_text or '').split()[1:]
    sender = event.sender_id
    usage = '用法：回复某人 /give 500，或 /give <用户 id> 500'

    replied = await event.get_reply_message()
    if replied and replied.sender_id:
        target = replied.sender_id
        amount_word = args[0] if args else ''
    elif len(args) >= 2:
        try:
            target = int(args[0])
        except ValueError:
            return await event.respond(usage)
        amount_word = args[1]
    else:
        return await event.respond(usage)

    if target == sender:
        return await event.respond('给自己转账没有意义。')

    try:
        amount = int(float(amount_word))
    except ValueError:
        return await event.respond(f'看不懂「{amount_word}」是多少钱。')
    if amount <= 0:
        return await event.respond('转账金额得是正数。')

    if not user_balance.transfer(sender, target, amount):
        return await event.respond(
            f'余额不足，你只有 {money(user_balance.get_balance(sender))}。')

    name = await bettor_name(event.client, target)
    return await event.respond(
        f'已转给 {name} **{money(amount)}**。\n'
        f'当前余额：**{money(user_balance.get_balance(sender))}**'
    )


def bankrupt_relief():
    """Every midnight, put the broke back in the game."""
    for user_id, balance in list(user_balance.balances.items()):
        if balance < MINIMUM_BALANCE:
            logging.info(f'[games]\tUser {user_id} at {balance}, granting {WELFARE_AMOUNT}')
            user_balance.add_balance(user_id, WELFARE_AMOUNT)
