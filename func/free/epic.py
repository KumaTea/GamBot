import json
import aiohttp


EPIC_FREE_API = (
    'https://store-site-backend-static-ipv4.ak.epicgames.com/freeGamesPromotions?'
    'locale=en-US&'
    'country=US&'
    'allowCountries=US'
)


async def get_epic_free_games_json() -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(EPIC_FREE_API) as resp:
            return json.loads(await resp.text())


def epic_free_games_list(games_json: dict) -> list[dict]:
    free_games = []
    games = games_json['data']['Catalog']['searchStore']['elements']
    for game in games:
        if '-' in game['productSlug']:
            free_games.append(game)
    return free_games


def epic_game_info(game_json: dict) -> dict:
    game_title = game_json['title']
    game_link = 'https://www.epicgames.com/store/en-US/p/' + game_json['productSlug']
    # game_price = game_json['price']['totalPrice']['fmtPrice']['originalPrice']
    # game_appid = game_json['id']
    game_info = {
        # 'id': int(game_appid),
        'name': game_title,
        'link': game_link,
        # 'price': game_price
    }
    return game_info
