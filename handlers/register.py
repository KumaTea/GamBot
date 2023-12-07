import logging
from bot.session import bot
from pyrogram import filters
from handlers.functions import *
from pyrogram.handlers import MessageHandler
from handlers.messages import private_message


def register_handlers():
    # group commands
    bot.add_handler(MessageHandler(command_stock, filters.command(['stock']) & filters.group))

    # gacha
    bot.add_handler(MessageHandler(command_gacha, filters.command(['gacha']) & filters.group))
    bot.add_handler(MessageHandler(command_gacha_genshin, filters.command(['gacha_ys', 'gacha_gs']) & filters.group))
    bot.add_handler(MessageHandler(command_gacha_arknights, filters.command(['gacha_ak', 'gacha_fz', 'gacha_mrfz']) & filters.group))
    bot.add_handler(MessageHandler(command_gacha_groupmem, filters.command(['gacha_group', 'gacha_grp', 'gacha_lp']) & filters.group))

    # games
    bot.add_handler(MessageHandler(command_baccarat, filters.command(['baccarat', 'bjl']) & filters.group))

    # admin commands
    bot.add_handler(MessageHandler(force_refresh, filters.command(['refresh']) & filters.group))

    # messages
    bot.add_handler(MessageHandler(private_message, filters.private))

    return logging.info('[handlers.register register_handlers]\tHandlers registered')


# def add_jobs():
#     scheduler.add_job(clean, 'cron', hour=4, minute=0)
#     scheduler.start()
#     return logging.info('[handlers.register manager]\tapscheduler started')
