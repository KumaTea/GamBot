from typing import Optional
from pyrogram import Client
from share.auth import ensure_auth
from share.common import no_preview
from games.balance import user_balance
from pyrogram.types import CallbackQuery
from func.games.betting import betting_state
from func.games.baccarat import format_betting_status


# Store temporary bet selections: {user_id: {'bet_type': str, 'amount': int}}
temp_bets = {}


@ensure_auth
async def handle_baccarat_callback(client: Client, callback: CallbackQuery) -> Optional[CallbackQuery]:
    """Handle baccarat betting callbacks"""
    if not callback.data or not callback.from_user:
        return None
    
    user_id = callback.from_user.id
    data_parts = callback.data.split('_')
    
    if len(data_parts) < 3:
        return None
    
    action = data_parts[0]
    chat_id = int(data_parts[1])
    
    # Check if betting is still open
    if not betting_state.is_betting_open(chat_id):
        await callback.answer('下注时间已结束！', show_alert=True)
        return None
    
    # Handle bet type selection
    if action == 'bet' and len(data_parts) == 3:
        bet_type = data_parts[2]  # 'player', 'banker', or 'tie'
        
        if user_id not in temp_bets:
            temp_bets[user_id] = {}
        temp_bets[user_id]['bet_type'] = bet_type
        
        bet_type_name = {'player': '闲家', 'banker': '庄家', 'tie': '和局'}[bet_type]
        await callback.answer(f'已选择：{bet_type_name}', show_alert=False)
        return None
    
    # Handle amount selection
    elif action == 'amount' and len(data_parts) == 3:
        amount_str = data_parts[2]
        
        if user_id not in temp_bets:
            temp_bets[user_id] = {'amount': 0}
        elif 'amount' not in temp_bets[user_id]:
            temp_bets[user_id]['amount'] = 0
        
        current_balance = user_balance.get_balance(user_id)
        current_amount = temp_bets[user_id]['amount']
        
        if amount_str == 'all':
            # Set to all available balance
            temp_bets[user_id]['amount'] = current_balance
            await callback.answer(f'已选择全部余额：{current_balance}', show_alert=False)
        else:
            # Accumulate amount
            add_amount = int(amount_str)
            new_amount = current_amount + add_amount
            
            # Don't exceed balance
            if new_amount > current_balance:
                temp_bets[user_id]['amount'] = current_balance
                await callback.answer(f'已达到最大余额：{current_balance}', show_alert=False)
            else:
                temp_bets[user_id]['amount'] = new_amount
                await callback.answer(f'已选择金额：{new_amount} (+{add_amount})', show_alert=False)
        
        return None
    
    # Handle bet cancellation
    elif action == 'cancel':
        if user_id in temp_bets:
            del temp_bets[user_id]
        await callback.answer('已取消下注', show_alert=False)
        return None
    
    # Handle bet confirmation
    elif action == 'confirm':
        if user_id not in temp_bets:
            await callback.answer('请先选择下注类型和金额！', show_alert=True)
            return None
        
        bet_info = temp_bets[user_id]
        if 'bet_type' not in bet_info or 'amount' not in bet_info or bet_info.get('amount', 0) <= 0:
            await callback.answer('请先选择下注类型和金额！', show_alert=True)
            return None
        
        bet_type = bet_info['bet_type']
        amount = bet_info['amount']
        
        # Check balance
        current_balance = user_balance.get_balance(user_id)
        if current_balance < amount:
            await callback.answer(f'余额不足！当前余额：{current_balance}', show_alert=True)
            return None
        
        # Place bet
        success = betting_state.place_bet(chat_id, user_id, bet_type, amount)
        if success:
            # Deduct balance immediately
            user_balance.subtract_balance(user_id, amount)
            bet_type_name = {'player': '闲家', 'banker': '庄家', 'tie': '和局'}[bet_type]
            new_balance = user_balance.get_balance(user_id)
            await callback.answer(
                f'下注成功！{bet_type_name} {amount} (余额: {new_balance})', 
                show_alert=True
            )
            # Clear temp bet
            if user_id in temp_bets:
                del temp_bets[user_id]
            
            # Update message to show new bet
            try:
                message = callback.message
                if message and message.text:
                    # Get current text and update betting status
                    current_text = message.text
                    # Find the betting status section and update it
                    lines = current_text.split('\n')
                    updated_lines = []
                    in_betting_section = False
                    for line in lines:
                        if '当前下注情况' in line:
                            in_betting_section = True
                            updated_lines.append(line)
                            # Add updated betting status
                            status_text = await format_betting_status(chat_id, client)
                            updated_lines.append(status_text)
                        elif in_betting_section and line.startswith('•'):
                            continue  # Skip old betting lines
                        elif '暂无下注' in line:
                            continue  # Skip this
                        elif in_betting_section and not line.startswith('•') and line.strip():
                            in_betting_section = False
                            updated_lines.append(line)
                        else:
                            updated_lines.append(line)
                    
                    updated_text = '\n'.join(updated_lines)
                    await message.edit_text(
                        updated_text,
                        **no_preview,
                        reply_markup=message.reply_markup
                    )
            except Exception:
                # If update fails, just continue
                pass
        else:
            await callback.answer('下注失败，请重试！', show_alert=True)
        
        return None
    
    return None
