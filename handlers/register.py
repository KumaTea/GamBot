import logging
from bot.session import bot
from pyrogram import filters
from handlers.functions import *
from pyrogram.handlers import MessageHandler


def register_handlers():
    # group commands
    bot.add_handler(MessageHandler(command_stock, filters.command(['stock']) & filters.group))

    return logging.info('[handlers.register register_handlers]\tHandlers registered')


# def add_jobs():
#     scheduler.add_job(clean, 'cron', hour=4, minute=0)
#     scheduler.start()
#     return logging.info('[handlers.register manager]\tapscheduler started')
