import logging
from pyrogram import Client
from share.common import no_quote
from pyrogram.types import Message
from share.auth import ensure_auth
from bot.tools import get_user_name
from games.balance import user_balance, WELFARE_AMOUNT, MINIMUM_BALANCE


@ensure_auth
async def command_balance(client: Client, message: Message) -> Message:
    """Check user's balance"""
    user = message.from_user
    if not user:
        return await message.reply_text('无法获取用户信息', **no_quote)
    
    user_id = user.id
    balance = user_balance.get_balance(user_id)
    user_name = get_user_name(user)
    
    text = f'{user_name} 的余额：**{balance}**'
    return await message.reply_text(text, **no_quote)


def bankrupt_relief():
    """At the start of a day, give relief to users below minimum balance"""
    for user_id, balance in user_balance.balances.items():
        if balance < MINIMUM_BALANCE:
            logging.info(f'User {user_id} balance {balance} below minimum. Adding welfare {WELFARE_AMOUNT}.')
            user_balance.add_balance(user_id, WELFARE_AMOUNT)
