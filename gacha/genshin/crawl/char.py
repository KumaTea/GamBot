import time
import json
import logging
import requests
from tqdm import tqdm
from bs4 import BeautifulSoup
from share.data import USER_AGENT
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


character_file = 'data/genshin/char.json'
character_url = 'https://wiki.biligame.com/ys/%E8%A7%92%E8%89%B2'
wiki_file_url = 'https://wiki.biligame.com/ys/%E6%96%87%E4%BB%B6:'

HEADERS = {'User-Agent': USER_AGENT}
TIMEOUT = 20
# a full refresh is a few hundred pages; the wiki starts dropping
# connections if they arrive as fast as the network allows
POLITE_DELAY = 0.2

# the wiki marks rarity with a class on the card wrapping each portrait
RARITY_CLASS = {5: 'C5星', 4: 'C4星'}

# the twins share one wiki page but roll as two characters
TWINS = {'空': '旅行者立绘3.png', '荧': '旅行者立绘2.png'}


def build_session() -> requests.Session:
    """One connection, reused, that retries the wiki's occasional resets."""
    session = requests.Session()
    session.headers.update(HEADERS)
    retry = Retry(
        total=4,
        backoff_factor=1,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(['GET']),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    return session


session = build_session()


def get(url: str) -> requests.Response:
    time.sleep(POLITE_DELAY)
    return session.get(url, timeout=TIMEOUT)


def character_page() -> BeautifulSoup:
    r = get(character_url)
    r.raise_for_status()
    return BeautifulSoup(r.text, 'html.parser')


def get_character_list(soup: BeautifulSoup = None) -> list[str]:
    """
    Every character named on the index page.

    Taken from the rarity cards rather than from the links: a link whose
    `title` matches its text is *usually* a character, but the same is
    true of half the navigation, and a card with stars on it never is.
    """
    soup = soup or character_page()
    return sorted(set(get_rarity_map(soup)) | set(TWINS))


def get_rarity_map(soup: BeautifulSoup = None) -> dict[str, int]:
    """Which characters the index page draws with five stars, and which four."""
    soup = soup or character_page()
    rarity = {}
    for stars, class_name in RARITY_CLASS.items():
        for card in soup.find_all(class_=class_name):
            for link in card.find_all('a'):
                # the wiki gives the traveler one card per element; the
                # two of them roll under their own names instead
                if link.get('title') == link.text and '旅行者' not in link.text:
                    rarity[link.text] = stars
    return rarity


def get_wiki_image_url(file: str) -> str:
    """
    The real file behind a wiki `文件:` page, not the thumbnail.

    Returns an empty string for anything that goes wrong: a refresh of
    a few hundred pictures should not be lost to one of them.
    """
    try:
        r = get(wiki_file_url + file)
    except requests.RequestException as e:
        logging.warning(f'[gacha]\tcould not read 文件:{file}: {e}')
        return ''
    if r.status_code != 200:
        return ''
    soup = BeautifulSoup(r.text, 'html.parser')
    link = (
        soup.find('a', string='原始文件')  # 立绘
        or
        soup.find('a', string=file)       # 头像
    )
    return link.get('href') if link else ''


def get_character_head_image(char: str) -> str:
    return get_wiki_image_url(f'无背景-角色-{char}.png')


def get_character_full_image(char: str) -> str:
    return get_wiki_image_url(TWINS.get(char) or f'{char}立绘.png')


def get_character_data(previous: dict = None) -> dict:
    """
    Rebuild the character pool from the wiki.

    Anything the wiki has stopped answering for keeps whatever url it
    had before, so one flaky page does not empty the pool.
    """
    previous = previous or {}
    soup = character_page()
    rarity = get_rarity_map(soup)
    chars = sorted(set(rarity) | set(TWINS))

    char_data = {}
    pbar = tqdm(chars)
    for char in pbar:
        pbar.set_description(char)
        was = previous.get(char, {})
        image = get_character_full_image(char)
        head = get_character_head_image(char)
        char_data[char] = {
            'name': char,
            # the twins are five stars and have no card of their own
            'rarity': rarity.get(char) or was.get('rarity') or (5 if char in TWINS else 4),
            'head': head or was.get('head', ''),
            'image': image or (was.get('image', '') if str(
                was.get('image', '')).startswith('http') else ''),
        }
    return char_data


def read_character_data() -> dict:
    try:
        with open(character_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def write_character_data(char_data: dict = None):
    if char_data is None:
        char_data = get_character_data(read_character_data())
    with open(character_file, 'w', encoding='utf-8') as f:
        json.dump(char_data, f, ensure_ascii=False, indent=2)
    return char_data


if __name__ == '__main__':
    write_character_data()
