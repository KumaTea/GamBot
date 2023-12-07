from pyrogram import Client
from pyrogram.types import Message
from common.info import administrators
from common.data import PHOTO_COMMIT_MSG
from gacha.groupmem.store import user_photos
from msg.photo import reply_photo_id, save_user_photo


# @ensure_not_bl
async def private_message(client: Client, message: Message) -> Message:
    if message.from_user and message.from_user.id in administrators and message.photo:
        if message.caption and message.caption.isdigit():
            return await save_user_photo(client, message)
        else:
            return await reply_photo_id(client, message)
    elif message.from_user and message.from_user.id in administrators and message.text:
        if message.text == PHOTO_COMMIT_MSG:
            user_photos.dump()
            return await message.reply_text('Dumped')
