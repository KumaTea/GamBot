from share.auth import ensure_auth
from telethon.tl.custom import Message
from func.games.dice import command_dice  # noqa -- re-exported for register.py
from func.games.slots import command_slots  # noqa
from func.games.baccarat import start_baccarat
from func.games.share import busy_notice  # noqa
from func.games.blackjack import command_blackjack  # noqa
from func.games.wallet import (  # noqa
    bankrupt_relief, command_balance, command_checkin,
    command_give, command_rank
)


HELP = """**赌场**

/baccarat 百家乐 — 全群下注，闲 1:1、庄 0.95:1、和 8:1
/blackjack 21点 — 单人对庄，可要牌、停牌、双倍
/slots 老虎机 — `/slots 500`，三个一样最高 120 倍
/dice 骰宝 — `/dice 大 500`，豹子 30:1

**钱**

/balance 查余额
/checkin 每日签到，连签有加成
/rank 富豪榜
/give 转账，回复某人 `/give 500`

破产了也不要紧，每天零点会发救济金。"""


@ensure_auth
async def command_games(event) -> Message:
    return await event.respond(HELP)


@ensure_auth
async def command_baccarat(event) -> Message:
    return await start_baccarat(event)
