import aiohttp
from bs4 import BeautifulSoup


STEAM_FREE_URL = 'https://store.steampowered.com/search/?sort_by=Price_ASC&ignore_preferences=1&specials=1&ndl=1'
GAMES_LIST_DIV_ID = 'search_resultsRows'
GAME_APPID_A_FIELD = 'data-ds-appid'
GAME_PAKID_A_FIELD = 'data-ds-packageid'
GAME_PRICE_DIV_CLASS = 'discount_final_price'
FREE_PRICES = ['¥0.00', '$0.00', '¥ 0.00', '$ 0.00']


async def steam_games_raw() -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(STEAM_FREE_URL) as resp:
            return await resp.text()


def steam_games_raw_list(html: str) -> list[str]:
    soup = BeautifulSoup(html, 'html.parser')
    games = soup.find(id=GAMES_LIST_DIV_ID)
    if not games:
        return []
    return games.find_all('a')


def steam_game_info(html: str) -> dict:
    soup = BeautifulSoup(html, 'html.parser')
    a_field = soup.find('a')
    if GAME_PAKID_A_FIELD in a_field.attrs:
        game_appid = a_field[GAME_PAKID_A_FIELD]
    else:
        game_appid = a_field[GAME_APPID_A_FIELD]
    # game_link = 'https://store.steampowered.com/app/' + game_appid
    game_link = a_field['href']
    game_name = soup.find('span', class_='title').text
    game_price = soup.find('div', class_=GAME_PRICE_DIV_CLASS).text
    game_info = {
        'id': int(game_appid),
        'name': game_name,
        'link': game_link,
        'price': game_price
    }
    return game_info


def steam_games_dict(raw_list: list[str]) -> dict[int, dict]:
    games_dict = {}
    for game in raw_list:
        game_info = steam_game_info(str(game))
        games_dict[game_info['id']] = game_info
    return games_dict


def steam_free_games_dict(games_dict: dict[int, dict]) -> dict[int, dict]:
    free_games_ids = []
    same_price_games_ids = []

    for game_id, game_info in games_dict.items():
        if not same_price_games_ids:
            same_price_games_ids.append(game_id)
            continue

        if any(price in game_info['price'] for price in FREE_PRICES):
            free_games_ids.append(game_id)
            continue

        if game_info['price'] == games_dict[same_price_games_ids[0]]['price']:
            same_price_games_ids.append(game_id)
            if len(same_price_games_ids) > 5:
                # all free games are found
                break
        else:
            free_games_ids.extend(same_price_games_ids)
            same_price_games_ids = [game_id]

    free_games_dict = {}
    for game_id in free_games_ids:
        free_games_dict[game_id] = games_dict[game_id]
    return free_games_dict
