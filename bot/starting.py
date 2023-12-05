import os
import logging
from common.data import *
from stock.tools import clear_cache
from handlers.register import register_handlers  # , add_jobs


def mkdir_p(paths: list):
    for path in paths:
        os.makedirs(path, exist_ok=True)


def starting():
    mkdir_p([STOCK_DATA_PATH])
    clear_cache()
    register_handlers()
    # add_jobs()

    return logging.info("[bot.starting starting]\tGamBot Initialized.")
