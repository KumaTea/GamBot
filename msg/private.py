from pyrogram import Client
from pyrogram.types import Message
from bot.auth import ensure_not_bl
from common.info import administrators
from msg.photo import reply_photo_id, save_user_photo


@ensure_not_bl
async def private_message(client: Client, message: Message) -> Message:
    if message.from_user and message.from_user.id in administrators and message.photo:
        if message.caption and message.caption.isdigit():
            return await save_user_photo(client, message)
        else:
            return await reply_photo_id(client, message)
