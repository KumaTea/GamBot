import random
import logging
import configparser
from telethon import TelegramClient
from apscheduler.schedulers.asyncio import AsyncIOScheduler


logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(module)12.12s:%(lineno)3d %(funcName)12.12s> %(message)s',
    level=logging.INFO,
    datefmt='%m-%d %H:%M:%S')

config = configparser.ConfigParser()
config.read('config.ini')

BOT_TOKEN = config['jd']['bot_token']

bot = TelegramClient(
    'jd',
    int(config['jd']['api_id']),
    config['jd']['api_hash'],
)

scheduler = AsyncIOScheduler()

urandom = random.SystemRandom()
