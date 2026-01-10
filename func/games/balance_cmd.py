from pyrogram import Client
from pyrogram.types import Message
from share.auth import ensure_auth
from bot.tools import get_user_name
from func.games.balance import user_balance


@ensure_auth
async def command_balance(client: Client, message: Message) -> Message:
    """Check user's balance"""
    user = message.from_user
    if not user:
        return await message.reply_text('无法获取用户信息', quote=False)
    
    user_id = user.id
    balance = user_balance.get_balance(user_id)
    user_name = get_user_name(user)
    
    text = f'{user_name} 的余额：**{balance}**'
    return await message.reply_text(text, quote=False)
