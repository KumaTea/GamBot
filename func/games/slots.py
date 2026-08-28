import asyncio
from typing import Optional
from share.auth import ensure_auth
from func.games.turns import in_turn
from func.fading import transient
from func.games.share import edit_text
from telethon.tl.custom import Message
from games.balance import money, settle_bet, signed
from func.games.wallet import bettor_name, take_stake
from games.slots import MAX_STAKE, MIN_STAKE, REELS, payout_rate, spin


GAME_NAME = '老虎机'
BLANK = '❓'
REEL_PAUSE = 0.8


def render(name: str, stake: int, shown: list, tail: str = '') -> str:
    window = ' | '.join(shown)
    return (
        f'**{GAME_NAME}** — {name}\n'
        f'投币 {money(stake)}\n\n'
        f'　【 {window} 】\n'
        f'{tail}'
    )


@ensure_auth
@transient
@in_turn
async def command_slots(event) -> Optional[Message]:
    args = (event.raw_text or '').split()[1:]
    stake, complaint = await take_stake(event, args[0] if args else '', MIN_STAKE, MAX_STAKE)
    if complaint:
        return complaint

    name = await bettor_name(event.client, event.sender_id)
    reels = spin()
    shown = [BLANK] * REELS

    message = await event.respond(render(name, stake, shown))
    # reveal one reel at a time -- the whole point of a slot machine is
    # the two seconds between the second and the third
    for i, face in enumerate(reels):
        await asyncio.sleep(REEL_PAUSE)
        shown[i] = face
        message = await edit_text(message, render(name, stake, shown))

    rate, what = payout_rate(reels)
    returned = int(stake * rate)
    balance, profit = settle_bet(event.sender_id, stake, returned)

    tail = (
        f'\n**{what}**\n'
        f'{signed(profit)}（余额 {money(balance)}）\n'
        f'\n/slots 再来一把！'
    )
    await asyncio.sleep(REEL_PAUSE)
    return await edit_text(message, render(name, stake, shown, tail))
