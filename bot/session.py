import logging
import configparser
from pyrogram import Client
from apscheduler.schedulers.asyncio import AsyncIOScheduler


logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(filename)15s:%(lineno)3s %(funcName)20s> %(message)s',
    level=logging.INFO,
    datefmt='%m-%d %H:%M:%S')

config = configparser.ConfigParser()
config.read('config.ini')
bot = Client(
    'jd',
    api_id=config['jd']['api_id'],
    api_hash=config['jd']['api_hash'],
    bot_token=config['jd']['bot_token'],
)

scheduler = AsyncIOScheduler()
