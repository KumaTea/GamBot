import logging
from typing import Union
from pyrogram import Client
from common.local import bl_users
from pyrogram.types import Message, CallbackQuery


def ensure_not_bl(func):
    async def wrapper(client: Client, obj: Union[Message, CallbackQuery]):
        if obj.from_user:
            user_id = obj.from_user.id
            if user_id in bl_users:
                logging.warning(f'User {user_id} is in blacklist! Ignoring message.')
                return None
        return await func(client, obj)
    return wrapper
