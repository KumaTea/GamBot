import asyncio
from pyrogram import Client
from bot.auth import ensure_auth
from pyrogram.types import Message
from func.free.steam import STEAM_FREE_URL
from func.free.epic import get_epic_free_games_json, epic_free_games_list, epic_game_info, EPIC_FREE_URL
from func.free.steam import steam_games_raw, steam_games_raw_list, steam_games_dict, steam_free_games_dict


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


@ensure_auth
async def command_free(client: Client, message: Message) -> Message:
    inform, steam, epic = await asyncio.gather(
        message.reply_text('正在获取...', quote=False),
        steam_free_games(),
        epic_free_games()
    )
    text = f'{steam}\n\n{epic}'
    return await inform.edit_text(text, disable_web_page_preview=True)
