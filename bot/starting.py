import os
import logging
from common.data import STOCK_DATA_DIR, USER_PHOTO_DIR
from handlers.register import add_jobs, register_handlers


def mkdir_p(paths: list):
    for path in paths:
        os.makedirs(path, exist_ok=True)


def starting():
    mkdir_p([USER_PHOTO_DIR, STOCK_DATA_DIR])
    register_handlers()
    add_jobs()

    return logging.info('GamBot Initialized.')
