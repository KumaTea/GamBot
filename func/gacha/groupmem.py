import logging
from typing import Optional
from pyrogram import Client
from common.data import bl_users
from func.gacha.tools import result_sender
from gacha.groupmem.main import grp_data, gacha
from pyrogram.types import User, Message, ChatMember
from bot.raw import get_user_profile_photo, send_photo


def get_user_name(user: User):
    lang = user.language_code or 'zh'
    if user.last_name:
        if user.last_name.encode().isalpha() and user.first_name.encode().isalpha():
            space = ' '
        else:
            space = ''
        if 'zh' in lang:
            return f'{user.first_name}{space}{user.last_name}'
        else:
            return f'{user.first_name}{space}{user.last_name}'
    else:
        return user.first_name


def is_qualified_user(member: ChatMember):
    user = member.user
    check_1 = user.id not in bl_users
    # check_2 = not user.is_bot
    check_3 = not user.is_deleted
    check_4 = user.photo
    check_5 = user.username
    return all([check_1, check_3, check_4, check_5])


async def retrieve_group_members(client: Client, message: Message):
    chat_id = message.chat.id
    members = []
    async for member in client.get_chat_members(chat_id):
        if is_qualified_user(member):
            members.append(member)
    grp_data.update(chat_id, members)


async def gacha_group_member(client: Client, message: Message) -> Optional[Message]:
    chat_id = message.chat.id
    if chat_id not in grp_data.groups:
        await retrieve_group_members(client, message)
    member = gacha(chat_id)
    user = member.user
    name = get_user_name(user)

    if user.id in grp_data.groups[chat_id]['photos']:
        photo = grp_data.groups[chat_id]['photos'][user.id]
    else:
        photo = await get_user_profile_photo(user.id)
        if photo:
            grp_data.groups[chat_id]['photos'][user.id] = photo

    if photo:
        logging.info(f'func.gacha.grp\t{name=}')
        msg_text = f'恭喜你抽中了群老婆 **{name}**！'
        await send_photo(
            chat_id=message.chat.id,
            photo=photo,
            caption=msg_text.replace('**', '*'),
            parse_mode='MarkdownV2'
        )
    else:
        msg_text = f'你抽中了 {name}，但是他不肯出来露脸，你可以重新抽一个。'
        return await message.reply_text(msg_text, quote=False)

