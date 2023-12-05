from typing import List
from propic.session import me
from bot.session import logging
from common.info import self_id
from common.data import bl_users
from telethon.tl.types import User


def is_qualified_user(user: User) -> bool:
    not_bl = user.id not in bl_users
    not_me = not user.is_self
    is_live = not user.deleted
    has_pic = user.photo
    has_un = user.username
    return not_bl and not_me and is_live and has_pic and has_un


async def get_chat_member(chat_id: int) -> List[User]:
    members = []
    for user in await me.get_participants(chat_id):
        if is_qualified_user(user):
            members.append(user)
    return members


async def get_user_photo(user: User) -> str:
    async for p in me.iter_profile_photos(user, limit=1):
        photo = p
        break
    else:
        photo = None
    return photo


async def send_chat_member_photos(chat_id: int):
    members = await get_chat_member(chat_id)
    for user in members:
        photo = await get_user_photo(user)
        if photo:
            await me.send_file(self_id, photo, caption=str(user.id))
            logging.info(f'propic.query\t{user.id=}')
