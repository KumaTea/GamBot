import logging
from typing import Optional
from share.auth import ensure_auth
from share.common import no_preview
from games.balance import money, user_balance
from func.games.betting import betting_state
from func.games.blackjack import handle_action
from func.games.baccarat import BET_NAMES, MAX_BET, MIN_BET, betting_buttons, render_betting


async def refresh(event, chat_id: int):
    """Redraw the betting message from the table, not from its own text."""
    state = betting_state.get(chat_id)
    if not state:
        return
    try:
        await event.edit(
            await render_betting(state, event.client),
            buttons=betting_buttons(chat_id),
            **no_preview
        )
    except Exception as e:
        logging.debug(f'[games]\tCould not refresh betting message: {e}')


@ensure_auth
async def handle_baccarat_callback(event) -> Optional[object]:
    """`bac:<chat id>:<action>:<value>`"""
    if not event.data or not event.sender_id:
        return None

    try:
        _, chat_id, action, value = event.data.decode().split(':', 3)
        chat_id = int(chat_id)
    except ValueError:
        return None

    user_id = event.sender_id
    if not betting_state.is_betting_open(chat_id):
        return await event.answer('下注时间已结束！', alert=True)

    # only the three actions that build a bet open a slot for one --
    # `no` has to be able to tell "nothing selected" from "selected
    # nothing", and creating the slot here would erase the difference
    pick = None
    if action in ('type', 'amt', 'ok'):
        pick = betting_state.pick(chat_id, user_id)
        if pick is None:
            return await event.answer('下注时间已结束！', alert=True)

    if action == 'type':
        if value not in BET_NAMES:
            return None
        pick.bet_type = value
        return await event.answer(f'已选择：{BET_NAMES[value]}')

    if action == 'amt':
        balance = user_balance.get_balance(user_id)
        ceiling = min(balance, MAX_BET)

        if value == 'all':
            pick.amount = int(ceiling)
            return await event.answer(f'梭哈：{money(pick.amount)}')

        try:
            step = int(value)
        except ValueError:
            return None
        wanted = pick.amount + step
        pick.amount = int(min(wanted, ceiling))
        if wanted > ceiling:
            return await event.answer(f'最多只能下 {money(pick.amount)}')
        return await event.answer(f'当前金额：{money(pick.amount)}（+{step}）')

    if action == 'no':
        # a selection that was never confirmed, first
        if betting_state.drop_pick(chat_id, user_id):
            return await event.answer('已取消选择')

        refund = betting_state.undo_bet(chat_id, user_id)
        if refund:
            user_balance.add_balance(user_id, refund)
            await event.answer(f'已撤回下注，退还 {money(refund)}')
            return await refresh(event, chat_id)
        return await event.answer('你还没有下注！')

    if action == 'ok':
        if not pick.bet_type or pick.amount <= 0:
            return await event.answer('请先选择下注类型和金额！', alert=True)
        if pick.amount < MIN_BET:
            return await event.answer(f'最少下注 {money(MIN_BET)}。', alert=True)

        # a change of mind gives the old stake back before taking the new one
        previous = betting_state.place_bet(chat_id, user_id, pick.bet_type, pick.amount)
        if previous is None:
            return await event.answer('下注时间已结束！', alert=True)
        if previous:
            user_balance.add_balance(user_id, previous)

        if not user_balance.subtract_balance(user_id, pick.amount):
            betting_state.undo_bet(chat_id, user_id)
            return await event.answer(
                f'余额不足！当前余额：{money(user_balance.get_balance(user_id))}', alert=True)

        betting_state.drop_pick(chat_id, user_id)
        await event.answer(
            f'下注成功！{BET_NAMES[pick.bet_type]} {money(pick.amount)}'
            f'（余额 {money(user_balance.get_balance(user_id))}）',
            alert=True
        )
        return await refresh(event, chat_id)

    if action == 'go':
        state = betting_state.get(chat_id)
        if not state:
            return None
        if user_id != state.opener:
            return await event.answer('只有开局的人可以提前开牌。')
        if not state.bets:
            return await event.answer('还没有人下注呢。')
        state.start_now = True
        return await event.answer('这就开牌！')

    return None


@ensure_auth
async def handle_blackjack_callback(event) -> Optional[object]:
    """`bj:<hand id>:<action>`"""
    if not event.data or not event.sender_id:
        return None
    try:
        _, hand_id, action = event.data.decode().split(':', 2)
        hand_id = int(hand_id)
    except ValueError:
        return None
    return await handle_action(event, hand_id, action)
