import asyncio
from pyrogram import Client
from bot.auth import ensure_not_bl
from pyrogram.types import Message
from func.free.steam import steam_games_raw, steam_games_raw_list, steam_games_dict, steam_free_games_dict


async def steam_free_games() -> str:
    text = 'Steam 免费 (疑似):\n'
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


@ensure_not_bl
async def command_free(client: Client, message: Message) -> Message:
    inform, steam = await asyncio.gather(
        message.reply_text('正在获取...', quote=False),
        steam_free_games()
    )
    text = f'{steam}'
    return await inform.edit_text(text, disable_web_page_preview=True)
