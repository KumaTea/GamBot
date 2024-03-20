from pyrogram import Client
from share.auth import ensure_auth
from pyrogram.types import Message
from func.games.baccarat import start_baccarat


@ensure_auth
async def command_baccarat(client: Client, message: Message) -> Message:
    return await start_baccarat(client, message)
