from pyrogram import Client
from pyrogram.types import Message
from func.games.baccarat import start_baccarat


async def command_baccarat(client: Client, message: Message) -> Message:
    return await start_baccarat(client, message)
