import os
import logging
from common.data import USER_PHOTO_DIR, STOCK_DATA_DIR
from handlers.register import register_handlers, add_jobs


def mkdir_p(paths: list):
    for path in paths:
        os.makedirs(path, exist_ok=True)


def starting():
    mkdir_p([USER_PHOTO_DIR, STOCK_DATA_DIR])
    register_handlers()
    add_jobs()

    return logging.info('GamBot Initialized.')
