import os
import logging
from handlers.register import add_jobs, register_handlers
from collect.store import COLLECT_BLOB_DIR, COLLECT_DATA_DIR
from common.data import STOCK_DATA_DIR
from bot.media_cache import MEDIA_DATA_DIR
from games.balance import BALANCE_DATA_DIR


DATA_DIRS = [
    STOCK_DATA_DIR,
    BALANCE_DATA_DIR,
    COLLECT_DATA_DIR,
    COLLECT_BLOB_DIR,
    MEDIA_DATA_DIR,
]


def mkdir_p(paths: list):
    for path in paths:
        os.makedirs(path, exist_ok=True)


def starting():
    mkdir_p(DATA_DIRS)
    register_handlers()
    add_jobs()

    return logging.info('GamBot Initialized.')
