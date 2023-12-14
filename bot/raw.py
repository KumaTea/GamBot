import aiohttp
import logging
from bot.session import config


bot_token = config['jd']['bot_token']


async def get_user_profile_photo(user_id: int):
    url = f'https://api.telegram.org/bot{bot_token}/getUserProfilePhotos'
    params = {
        'user_id': user_id,
        'limit': 1
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            data = await resp.json()
    # logging.info(f'{data=}')
    if data['ok']:
        photos = data['result']['photos']
        if photos:
            file_id = photos[0][0]['file_id']
            return file_id
    return None


async def send_photo(chat_id: int, photo: str, caption: str = None, parse_mode: str = None):
    url = f'https://api.telegram.org/bot{bot_token}/sendPhoto'
    params = {
        'chat_id': chat_id,
        'photo': photo,
        'caption': caption,
        'parse_mode': parse_mode
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                data = await resp.json()
    except Exception as e:
        logging.error(f'{e=}')
        logging.error(f'{url=} {params=}')
        logging.error(f'{data=}')
        data = None
    return data
