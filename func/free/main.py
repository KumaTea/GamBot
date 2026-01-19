import asyncio
import aiohttp
from pyrogram import Client
from share.auth import ensure_auth
from pyrogram.types import Message
from share.common import no_quote, no_preview
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
            count = 0
            for game_info in free_games_dict.values():
                count += 1
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
            count = 0
            for game_json in free_games_list:
                count += 1
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
    except:
        await asyncio.sleep(2)


@ensure_auth
async def command_free(client: Client, message: Message) -> Message:
    inform, _ = await asyncio.gather(
        message.reply_text('正在测试网络...', **no_quote),
        test_network()
    )
    steam, epic = await asyncio.gather(
        steam_free_games(),
        epic_free_games()
    )
    text = f'{steam}\n\n{epic}'
    return await inform.edit_text(text, **no_preview)
