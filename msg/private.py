from pyrogram import Client
from pyrogram.types import Message
from bot.auth import ensure_not_bl
from common.info import administrators


async def reply_photo_id(client: Client, message: Message) -> Message:
    photo = message.photo
    photo_id = photo.file_id
    return await message.reply_text(f'`{photo_id}`')


@ensure_not_bl
async def private_message(client: Client, message: Message) -> Message:
    if message.from_user and message.from_user.id in administrators and message.photo:
        return await reply_photo_id(client, message)
