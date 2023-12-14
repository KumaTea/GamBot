import random
import asyncio
from typing import Optional
from pyrogram import Client
from bot.tools import get_user_name
from common.data import BACCARAT_RULE
from pyrogram.types import Message, Chat
from func.games.share import game_status
from games.cards.card import generate_deck
from games.cards.baccarat import BaccaratDeck, Card, player_should_draw, banker_should_draw


class GameTable:
    def __init__(self):
        self.groups = {}


game_table = GameTable()


async def message_edit(message: Message, text: str, sleep_time: float = 1) -> Message:
    reply = await message.edit_text(text, disable_web_page_preview=True)
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
    text = f'{user_name} 开了一局百家乐！\n'
    reply = await message.reply_text(text, quote=False)
    game_status.set_in_game(chat_id, '百家乐', reply.id)
    await asyncio.sleep(5)
    text_1 = '现在是下注时间 (该功能未实装)\n'
    text = text + text_1
    reply = await message_edit(reply, text, 5)
    text_2 = '下注时间已结束\n'
    text = text + text_2
    reply = await message_edit(reply, text, 5)

    # get the deck ready
    if chat_id not in game_table.groups or len(game_table.groups[chat_id]) < 6:
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
    banker_card_1 = deck.deal()
    text += f'闲家的第一张牌是{player_card_1}，庄家的第一张牌是{banker_card_1}。\n'
    reply = await message_edit(reply, text, 2)
    player_card_2 = deck.deal()
    banker_card_2 = deck.deal()
    player_value = player_card_1.value + player_card_2.value
    player_value = int(str(player_value)[-1])
    banker_value = banker_card_1.value + banker_card_2.value
    banker_value = int(str(banker_value)[-1])
    text += f'闲家的牌是{player_card_1}和{player_card_2}，总点数是{player_value}。\n'
    reply = await message_edit(reply, text, 2)
    text += f'庄家的牌是{banker_card_1}和{banker_card_2}，总点数是{banker_value}。\n'
    reply = await message_edit(reply, text, 2)

    if player_value >= 8 or banker_value >= 8:
        text += f'有一家得分超过8，双方[不需要补牌]({BACCARAT_RULE})！\n'
        reply = await message_edit(reply, text, 2)
    else:
        player_card_3 = Card('A')  # dummy card
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
        result = '闲家获胜'
    elif player_value < banker_value:
        result = '庄家获胜'
    else:
        result = '和局'
    text += f'\n结果是：**{result}**！\n'
    reply = await message_edit(reply, text, 2)
    game_status.game_over(chat_id)
    return reply
