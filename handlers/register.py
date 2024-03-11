import logging
from pyrogram import filters
from handlers.functions import *
from bot.session import bot, scheduler
from pyrogram.handlers import MessageHandler
from handlers.messages import private_message


def register_handlers():
    # group commands

    # stock
    bot.add_handler(MessageHandler(command_stock, filters.command(['stock']) & filters.group))
    bot.add_handler(MessageHandler(command_remind_stock, filters.command(['remind_stock']) & filters.group))
    bot.add_handler(MessageHandler(command_forget_stock, filters.command(['forget_stock']) & filters.group))

    # gacha
    bot.add_handler(MessageHandler(command_gacha, filters.command(['gacha']) & filters.group))
    bot.add_handler(MessageHandler(command_gacha_genshin, filters.command(['gacha_ys', 'gacha_gs']) & filters.group))
    bot.add_handler(MessageHandler(command_gacha_arknights, filters.command(['gacha_ak', 'gacha_fz', 'gacha_mrfz']) & filters.group))
    bot.add_handler(MessageHandler(command_gacha_groupmem, filters.command(['gacha_group', 'gacha_grp', 'gacha_lp']) & filters.group))

    # games
    bot.add_handler(MessageHandler(command_free, filters.command(['free', 'free_games']) & filters.group))
    bot.add_handler(MessageHandler(command_baccarat, filters.command(['baccarat', 'bjl']) & filters.group))

    # stickers
    bot.add_handler(MessageHandler(command_bro, filters.command(['bro']) & filters.group))

    # admin commands
    bot.add_handler(MessageHandler(force_refresh, filters.command(['refresh']) & filters.group))

    # messages
    bot.add_handler(MessageHandler(private_message, filters.private))

    return logging.info('Handlers registered')


def add_jobs():
    scheduler.add_job(remind_stock_all, 'cron', hour=14, minute=55)
    scheduler.add_job(remind_free, 'cron', hour=0, minute=5)
    scheduler.start()
    return logging.info('apscheduler started')
