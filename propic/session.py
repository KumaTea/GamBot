import os
import time
import argparse
from pathlib import Path
from telethon import TelegramClient
from bot.session import config, logging


arg_parser = argparse.ArgumentParser()
arg_parser.add_argument('--chat-id', type=int)

me = TelegramClient(
    'me',
    config['jd']['api_id'],
    config['jd']['api_hash']
)


class StatHolder:
    def __init__(self, sign: str, delay: int = 1):
        self.sign = sign
        self.delay = delay
        self.pid = os.getpid()

    def __enter__(self):
        while os.path.isfile(self.sign):
            logging.info(f'User bot pid={self.pid} waiting...')
            time.sleep(self.delay)
        Path(self.sign).touch()
        logging.info(f'User bot pid={self.pid} started!')

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.remove(self.sign)
        logging.info(f'User bot pid={self.pid} stopped.')
