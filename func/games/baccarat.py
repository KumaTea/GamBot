import random
import asyncio
from typing import Optional
from pyrogram import Client
from bot.tools import get_user_name
from common.data import BACCARAT_RULE
from func.games.share import game_status
from func.games.balance import user_balance
from func.games.betting import betting_state
from games.cards.card import Card, generate_deck
from games.cards.baccarat import BaccaratDeck, banker_should_draw, player_should_draw
from pyrogram.types import Chat, Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup


class GameTable:
    def __init__(self):
        self.groups = {}


game_table = GameTable()


async def message_edit(message: Message, text: str, sleep_time: float = 1, reply_markup=None) -> Message:
    reply = await message.edit_text(text, disable_web_page_preview=True, reply_markup=reply_markup)
    await asyncio.sleep(sleep_time)
    return reply


def gen_baccarat_deck() -> BaccaratDeck:
    deck = generate_deck()
    deck *= 8
    return BaccaratDeck(deck=deck)


def get_msg_link(chat: Chat, msg_id: int) -> str:
    if chat.username:
        return f'https://t.me/{chat.username}/{msg_id}'
    else:
        chat_id = chat.id
        chat_id_str = str(chat_id).replace('-100', '')
        return f'https://t.me/c/{chat_id_str}/{msg_id}'


def create_betting_keyboard(chat_id: int) -> InlineKeyboardMarkup:
    """Create betting buttons"""
    bet_amounts = [10, 50, 100, 500]
    keyboard = []
    
    # Bet type buttons
    keyboard.append([
        InlineKeyboardButton("闲家 (1:1)", callback_data=f"bet_{chat_id}_player"),
        InlineKeyboardButton("庄家 (0.95:1)", callback_data=f"bet_{chat_id}_banker"),
        InlineKeyboardButton("和局 (8:1)", callback_data=f"bet_{chat_id}_tie")
    ])
    
    # Amount buttons
    amount_row = []
    for amount in bet_amounts:
        amount_row.append(InlineKeyboardButton(f"{amount}", callback_data=f"amount_{chat_id}_{amount}"))
    keyboard.append(amount_row)
    
    keyboard.append([InlineKeyboardButton("确认下注", callback_data=f"confirm_{chat_id}_0")])
    
    return InlineKeyboardMarkup(keyboard)


async def format_betting_status(chat_id: int, client: Client = None) -> str:
    """Format current betting status"""
    bets = betting_state.get_bets(chat_id)
    if not bets:
        return "暂无下注" + "\n"
    
    status_lines = []
    for user_id, bet_info in bets.items():
        bet_type = bet_info['bet_type']
        amount = bet_info['amount']
        bet_type_name = {'player': '闲家', 'banker': '庄家', 'tie': '和局'}[bet_type]
        # Try to get user name if client is available
        user_name = f"用户{user_id}"
        if client:
            try:
                user = await client.get_users(user_id)
                user_name = get_user_name(user)
            except Exception:
                pass
        status_lines.append(f"• {user_name}: {bet_type_name} {amount}")
    
    return ("\n".join(status_lines) if status_lines else "暂无下注") + "\n"


async def start_baccarat(client: Client, message: Message) -> Optional[Message]:
    chat_id = message.chat.id
    user = message.from_user
    if not user:
        return None
    if chat_id in game_status.groups:
        game = game_status.groups[chat_id]['game']
        msg_link = get_msg_link(message.chat, game_status.groups[chat_id]['msg_id'])
        return await message.reply_text(
            f'本群正在玩{game}，[这局]({msg_link})结束后才能开始！',
            quote=False,
            disable_web_page_preview=True
        )

    # announce
    user_name = get_user_name(user)
    user_balance_amount = user_balance.get_balance(user.id)
    text = f'{user_name} 开了一局百家乐！\n'
    # text += f'当前余额：**{user_balance_amount}**\n\n'
    
    # Start betting phase
    betting_state.start_betting(chat_id, 0)  # msg_id will be set after reply
    betting_keyboard = create_betting_keyboard(chat_id)
    
    text += '现在是下注时间！\n'
    text += '请选择下注类型和金额。\n\n'
    text += '**当前下注情况：**\n'
    text += await format_betting_status(chat_id, client)
    
    reply = await message.reply_text(
        text, 
        quote=False, 
        reply_markup=betting_keyboard
    )
    game_status.set_in_game(chat_id, '百家乐', reply.id)
    betting_state.game_data[chat_id]['msg_id'] = reply.id
    
    # Wait for betting (30 seconds)
    await asyncio.sleep(30)
    
    # Close betting
    betting_state.close_betting(chat_id)
    text += '\n\n下注时间已结束！\n'
    text += '**最终下注情况：**\n'
    text += await format_betting_status(chat_id, client)
    reply = await message_edit(reply, text, 2, reply_markup=None)

    # get the deck ready
    if chat_id not in game_table.groups or len(current_deck := game_table.groups[chat_id]) < 6:
        deck = gen_baccarat_deck()
        text += '发牌箱是空的。荷官拿了8副牌过来。\n'
        reply = await message_edit(reply, text, 5)

        shuffle_times = random.randint(1, 10)
        for _ in range(shuffle_times):
            deck.shuffle()
        game_table.groups[chat_id] = deck
        await asyncio.sleep(shuffle_times)
        text += f'荷官把牌洗了{shuffle_times}次，放进了发牌箱。\n'
        reply = await message_edit(reply, text, 5)

    deck = game_table.groups[chat_id]
    # 第一及第三张牌发给“闲家”，第二及第四张牌则发给“庄家”。
    player_card_1 = deck.deal()
    text += f'闲家的第一张牌是{player_card_1}。\n'
    reply = await message_edit(reply, text, 2)
    banker_card_1 = deck.deal()
    text += f'庄家的第一张牌是{banker_card_1}。\n'
    reply = await message_edit(reply, text, 2)
    player_card_2 = deck.deal()
    banker_card_2 = deck.deal()
    player_value = player_card_1.value + player_card_2.value
    player_value = int(str(player_value)[-1])
    banker_value = banker_card_1.value + banker_card_2.value
    banker_value = int(str(banker_value)[-1])
    text += f'闲家第二张是{player_card_2}，{player_card_1}和{player_card_2}的点数是{player_value}。\n'
    reply = await message_edit(reply, text, 2)
    text += f'庄家第二张是{banker_card_2}，{banker_card_1}和{banker_card_2}的点数是{banker_value}。\n'
    reply = await message_edit(reply, text, 2)

    if player_value >= 8 or banker_value >= 8:
        text += f'有一家得分超过8，双方[不需要补牌]({BACCARAT_RULE})！\n'
        reply = await message_edit(reply, text, 2)
    else:
        player_card_3 = Card('A', 'S')  # dummy card
        if player_should_draw(player_value):
            player_card_3 = deck.deal()
            player_value += player_card_3.value
            player_value = int(str(player_value)[-1])
            text += f'闲家[需要补牌]({BACCARAT_RULE})！补到了{player_card_3}，总点数是{player_value}。\n'
        else:
            text += F'闲家[不需要补牌]({BACCARAT_RULE})。\n'
        reply = await message_edit(reply, text, 2)

        if banker_should_draw(player_should_draw(player_value), player_card_3.value, banker_value):
            banker_card_3 = deck.deal()
            banker_value += banker_card_3.value
            banker_value = int(str(banker_value)[-1])
            text += f'庄家[需要补牌]({BACCARAT_RULE})！补到了{banker_card_3}，总点数是{banker_value}。\n'
        else:
            text += F'庄家[不需要补牌]({BACCARAT_RULE})。\n'
        reply = await message_edit(reply, text, 2)

    if player_value > banker_value:
        result = 'player'
        result_text = '闲家获胜'
    elif player_value < banker_value:
        result = 'banker'
        result_text = '庄家获胜'
    else:
        result = 'tie'
        result_text = '和局'
    
    # Store game result
    betting_state.set_game_result(chat_id, result, player_value, banker_value)
    
    text += f'\n结果是：**{result_text}**！\n'
    reply = await message_edit(reply, text, 2)
    
    # Process bets and update balances
    bets = betting_state.get_bets(chat_id)
    if bets:
        text += '\n**结算结果：**\n'
        for user_id, bet_info in bets.items():
            bet_type = bet_info['bet_type']
            amount = bet_info['amount']
            
            # Get user name
            try:
                user = await client.get_users(user_id)
                user_name = get_user_name(user)
            except Exception:
                user_name = f"用户{user_id}"
            
            if bet_type == result:
                # Win
                if result == 'player':
                    winnings = amount * 2  # 1:1 payout
                elif result == 'banker':
                    winnings = int(amount * 1.95)  # 0.95:1 payout (rounded down)
                else:  # tie
                    winnings = amount * 9  # 8:1 payout
                
                profit = winnings  # - amount
                new_balance = user_balance.add_balance(user_id, profit)
                bet_type_name = {'player': '闲家', 'banker': '庄家', 'tie': '和局'}[bet_type]
                text += f'✓ {user_name}: 下注{bet_type_name} {amount} → 赢得 {winnings} (余额: {new_balance})\n'
            else:
                # Loss
                new_balance = user_balance.get_balance(user_id)  # Already deducted when bet was placed
                bet_type_name = {'player': '闲家', 'banker': '庄家', 'tie': '和局'}[bet_type]
                text += f'✗ {user_name}: 下注{bet_type_name} {amount} → 输掉 (余额: {new_balance})\n'

    text += '\n' + '点击 /baccarat 再来一局！'
    reply = await message_edit(reply, text, 2)
    
    # Clean up
    betting_state.clear_game(chat_id)
    game_status.game_over(chat_id)

    return reply
