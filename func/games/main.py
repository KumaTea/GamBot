from func.games.baccarat import start_baccarat
from pyrogram import Client
from pyrogram.types import Message


async def command_baccarat(client: Client, message: Message) -> Message:
    return await start_baccarat(client, message)
