import asyncio
import logging
from typing import Optional
from pyrogram import Client
from bot.tools import get_user_name
from gacha.groupmem.store import user_photos
from pyrogram.types import Message, ChatMember
from gacha.groupmem.main import gacha, grp_data
from common.local import bl_users, trusted_group
from bot.raw import send_photo, get_user_profile_photo


def is_qualified_user(member: ChatMember):
    user = member.user
    not_bl = user.id not in bl_users
    not_me = not user.is_self
    is_live = not user.is_deleted
    has_pic = user.photo
    has_un = user.username
    return not_bl and not_me and is_live and has_pic and has_un


async def retrieve_group_members(client: Client, message: Message):
    chat_id = message.chat.id
    members = []
    async for member in client.get_chat_members(chat_id):
        if is_qualified_user(member):
            members.append(member)
    grp_data.update(chat_id, members)


async def run_pic_bot(chat_id: int, forced: bool = False):
    if forced or (chat_id not in user_photos.groups and chat_id in trusted_group):
        command = '/opt/conda/envs/jd/bin/python3 propicbot.py --chat-id ' + str(chat_id)
        proc = await asyncio.create_subprocess_shell(command)
        user_photos.register_group(chat_id)
        # don't wait
        return proc


async def gacha_group_member(client: Client, message: Message) -> Optional[Message]:
    chat_id = message.chat.id
    if chat_id not in grp_data.groups:
        await asyncio.gather(
            retrieve_group_members(client, message),
            run_pic_bot(chat_id)
        )
    member = gacha(chat_id)
    user = member.user
    name = member.custom_title or get_user_name(user)

    photo = None
    raw_photo = None
    if user.id in user_photos.photos:
        photo = user_photos.photos[user.id]
    else:
        raw_photo = await get_user_profile_photo(user.id)

    if user.is_bot:
        user_type = '机器'
    else:
        user_type = '群'

    logging.info(f'{name=}')
    msg_text = f'恭喜你抽中了{user_type}老婆 **{name}**！'
    if photo:
        try:
            return await message.reply_photo(
                photo=photo,
                caption=msg_text,
                quote=False
            )
        except ValueError:
            raw_photo = photo
    if raw_photo:
        data = await send_photo(
            chat_id=message.chat.id,
            photo=raw_photo,
            caption=msg_text.replace('**', '*'),
            parse_mode='MarkdownV2'
        )
        if data['ok']:
            file_id = data['result']['photo'][0]['file_id']
            user_photos.update(user.id, file_id)
            return None
    else:
        msg_text = f'你抽中了 {name}，但是他不肯出来露脸，你可以重新抽一个。'
        return await message.reply_text(msg_text, quote=False)
