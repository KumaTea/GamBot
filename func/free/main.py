import asyncio
import aiohttp
from share.auth import ensure_auth
from share.common import no_preview
from telethon.tl.custom import Message
from func.free.epic import EPIC_FREE_URL, EPIC_FREE_API, epic_game_info, epic_free_games_list, get_epic_free_games_json
from func.free.steam import STEAM_FREE_URL, steam_games_raw, steam_games_dict, steam_games_raw_list, steam_free_games_dict


async def steam_free_games() -> str:
    text = f'[Steam 免费]({STEAM_FREE_URL}): \n'
    try:
        games_raw = await steam_games_raw()
        games_raw_list = steam_games_raw_list(games_raw)
        games_dict = steam_games_dict(games_raw_list)
        free_games_dict = steam_free_games_dict(games_dict)
        if free_games_dict:
            for count, game_info in enumerate(free_games_dict.values(), start=1):
                text += f'  {count}. [{game_info["name"]}]({game_info["link"]})\n'
        else:
            text += '    暂无'
    except Exception as e:
        text += f'    获取失败: {e}'
    return text


async def epic_free_games() -> str:
    text = f'[Epic Games 免费]({EPIC_FREE_URL}): \n'
    try:
        free_games_json = await get_epic_free_games_json()
        free_games_list = epic_free_games_list(free_games_json)
        if free_games_list:
            for count, game_json in enumerate(free_games_list, start=1):
                game_info = epic_game_info(game_json)
                text += f'  {count}. [{game_info["name"]}]({game_info["link"]})\n'
        else:
            text += '    暂无'
    except Exception as e:
        text += f'    获取失败: {e}'
    return text


async def test_network() -> None:
    try:
        async with aiohttp.ClientSession() as session:
            tasks = [
                session.get(EPIC_FREE_API),
                session.get(EPIC_FREE_URL),
                session.get(STEAM_FREE_URL)
            ]
            await asyncio.gather(*tasks)
    except Exception:
        await asyncio.sleep(2)


@ensure_auth
async def command_free(event) -> Message:
    inform, _ = await asyncio.gather(
        event.respond('正在获取...'),
        test_network()
    )
    steam, epic = await asyncio.gather(
        steam_free_games(),
        epic_free_games()
    )
    text = f'{steam}\n\n{epic}'
    return await inform.edit(text, **no_preview)
