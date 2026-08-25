import logging
from telethon import events
from common.info import username
from share.common import command_re
from bot.session import bot, scheduler
from handlers.functions import *  # noqa
from handlers.messages import private_message, watch_messages
from func.collect.main import collection_commands
from func.games.callbacks import handle_baccarat_callback, handle_blackjack_callback


in_group = (lambda e: e.is_group)
in_private = (lambda e: e.is_private)


def on_command(callback, commands: list[str], where=None):
    bot.add_event_handler(callback, events.NewMessage(
        incoming=True,
        pattern=command_re(commands, username),
        func=where
    ))


def on_callback(callback, prefix: str):
    bot.add_event_handler(callback, events.CallbackQuery(
        pattern=f'^{prefix}:'.encode()
    ))


def register_handlers():
    # group commands

    # stock
    on_command(command_stock, ['stock', '股票', '大盘'], in_group)
    on_command(command_remind_stock, ['remind_stock'], in_group)
    on_command(command_forget_stock, ['forget_stock'], in_group)

    # paper trading
    on_command(command_buy, ['buy', '买入', '买'], in_group)
    on_command(command_sell, ['sell', '卖出', '卖'], in_group)
    on_command(command_position, ['position', 'hold', '持仓'], in_group)

    # gacha
    on_command(command_gacha, ['gacha'], in_group)
    on_command(command_gacha_genshin, ['gacha_ys', 'gacha_gs'], in_group)
    on_command(command_gacha_arknights, ['gacha_ak', 'gacha_fz', 'gacha_mrfz'], in_group)

    # games
    on_command(command_free, ['free', 'free_games'], in_group)
    on_command(command_games, ['games', '赌场'], in_group)
    on_command(command_baccarat, ['baccarat', 'bjl', '百家乐'], in_group)
    on_command(command_blackjack, ['blackjack', 'bj', '21点'], in_group)
    on_command(command_slots, ['slots', 'slot', '老虎机'], in_group)
    on_command(command_dice, ['dice', 'sicbo', '骰宝'], in_group)

    # money
    on_command(command_balance, ['balance', 'money', '余额'], in_group)
    on_command(command_checkin, ['checkin', 'sign', '签到'], in_group)
    on_command(command_rank, ['rank', 'top', '富豪榜'], in_group)
    on_command(command_give, ['give', 'transfer', '转账'], in_group)

    on_callback(handle_baccarat_callback, 'bac')
    on_callback(handle_blackjack_callback, 'bj')

    # stickers
    on_command(command_bro, ['bro'], in_group)

    # picture collections -- one command per collection. No `in_group`:
    # filing a picture by replying to it works in the bot's own chat too
    for collection, command in collection_commands.items():
        on_command(command, [collection])

    # everything else in a group, so a keyword can file the picture
    # that came before it
    bot.add_event_handler(watch_messages, events.NewMessage(
        incoming=True,
        func=in_group
    ))

    # messages
    bot.add_event_handler(private_message, events.NewMessage(
        incoming=True,
        func=in_private
    ))

    return logging.info('Handlers registered')


def add_jobs():
    scheduler.add_job(remind_stock_all, 'cron', hour=14, minute=55)
    scheduler.add_job(remind_free, 'cron', hour=0, minute=5)
    scheduler.add_job(bankrupt_relief, 'cron', hour=0, minute=5)
    scheduler.start()
    return logging.info('apscheduler started')
