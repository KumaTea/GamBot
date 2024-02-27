import json
import aiohttp
from datetime import datetime, timezone, timedelta


EPIC_FREE_API = (
    'https://store-site-backend-static-ipv4.ak.epicgames.com/freeGamesPromotions'
    # '?'
    # 'locale=en-US&'
    # 'country=US&'
    # 'allowCountries=US'
)
EPIC_FREE_URL = 'https://store.epicgames.com/en-US/free-games'


async def get_epic_free_games_json() -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(EPIC_FREE_API) as resp:
            return json.loads(await resp.text())


def get_game_link(game_json: dict) -> str:
    if (
        'productSlug' in game_json and
        game_json['productSlug'] and
        '-' in game_json['productSlug']
    ):
        return 'https://www.epicgames.com/store/en-US/p/' + game_json['productSlug']
    if (
        'offerMappings' in game_json and
        game_json['offerMappings'] and
        'pageSlug' in game_json['offerMappings'][0] and
        '-' in game_json['offerMappings'][0]['pageSlug']
    ):
        return 'https://www.epicgames.com/store/en-US/p/' + game_json['offerMappings'][0]['pageSlug']
    else:
        return ''


def epic_free_games_list(games_json: dict) -> list[dict]:
    valid_games = []
    free_games = []
    games = games_json['data']['Catalog']['searchStore']['elements']
    for game in games:
        if get_game_link(game):
            valid_games.append(game)
    for game in valid_games:
        promotions = game['promotions']
        if not promotions:
            continue
        offers = promotions['promotionalOffers']
        if not offers:
            continue
        while 'promotionalOffers' in offers[0]:
            offers = offers[0]['promotionalOffers']
            if not offers:
                continue
        for offer in offers:
            if offer['discountSetting']['discountPercentage'] != 0:
                continue
            start_date = datetime.fromisoformat(offer['startDate'])
            end_date = datetime.fromisoformat(offer['endDate'])
            now = datetime.now(timezone(timedelta(hours=8)))
            if start_date <= now <= end_date:
                free_games.append(game)
    return free_games


def epic_game_info(game_json: dict) -> dict:
    game_title = game_json['title']
    game_link = get_game_link(game_json)
    # game_price = game_json['price']['totalPrice']['fmtPrice']['originalPrice']
    # game_appid = game_json['id']
    game_info = {
        # 'id': int(game_appid),
        'name': game_title,
        'link': game_link,
        # 'price': game_price
    }
    return game_info
