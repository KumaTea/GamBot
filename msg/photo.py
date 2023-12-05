import asyncio
from pyrogram import Client
from pyrogram.types import Message
from gacha.groupmem.store import user_photos


async def reply_photo_id(client: Client, message: Message) -> Message:
    photo = message.photo
    photo_id = photo.file_id
    return await message.reply_text(f'`{photo_id}`')


async def save_user_photo(client: Client, message: Message):
    photo = message.photo
    caption = message.caption
    photo_id = photo.file_id
    user_id = int(caption)
    user_photos.save(user_id, photo_id)
    return await asyncio.gather(
        message.reply_text(f'Saved {user_id=}'),
        message.delete()
    )
