import random
from share.auth import ensure_auth
from telethon.tl.custom import Message
from share.common import get_command_args
from func.gacha.genshin import gacha_genshin
from func.gacha.arknights import gacha_arknights
from common.data import GACHA_GENSHIN_CMD, GACHA_ARKNIGHTS_CMD


POOLS = {
    'genshin': (GACHA_GENSHIN_CMD, gacha_genshin),
    'arknights': (GACHA_ARKNIGHTS_CMD, gacha_arknights),
}


@ensure_auth
async def command_gacha(event) -> Message:
    """`/gacha` for whichever pool comes up, `/gacha ys` for a named one."""
    args = get_command_args(event.raw_text)
    if not args:
        _, roll = POOLS[random.choice(list(POOLS))]
        return await roll(event)

    wanted = args[0].lower()
    for names, roll in POOLS.values():
        if wanted in names:
            return await roll(event)

    pools = '、'.join(sorted(n for names, _ in POOLS.values() for n in list(names)[:2]))
    return await event.respond(f'找不到指定的池子！可以试试：{pools}')


@ensure_auth
async def command_gacha_genshin(event) -> Message:
    return await gacha_genshin(event)


@ensure_auth
async def command_gacha_arknights(event) -> Message:
    return await gacha_arknights(event)
