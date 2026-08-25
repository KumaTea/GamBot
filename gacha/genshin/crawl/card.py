import json
from tqdm import tqdm
from bs4 import BeautifulSoup
from gacha.genshin.crawl.char import get, get_wiki_image_url


cards_file = r'data/genshin/card.json'
cards_url = 'https://wiki.biligame.com/ys/%E5%8D%A1%E7%89%8C%E4%B8%80%E8%A7%88'

CARD_PREFIX = '卡牌：'
# 七圣召唤 has character cards and action cards; only the first kind has
# a portrait, and the file name is the only thing that tells them apart
ART_FILE = '卡牌-角色牌-{name}.png'


def get_card_names() -> list[str]:
    """Every card the index page links to, action cards included."""
    r = get(cards_url)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, 'html.parser')
    names = {
        a['title'][len(CARD_PREFIX):]
        for a in soup.find_all('a')
        if a.get('title', '').startswith(CARD_PREFIX)
    }
    return sorted(n for n in names if n)


def get_card_image(name: str) -> str:
    return get_wiki_image_url(ART_FILE.format(name=name))


def read_cards() -> dict:
    try:
        with open(cards_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def get_cards(previous: dict = None) -> dict:
    """
    Rebuild the character-card pool.

    Names already on file are looked up first so a run that dies part
    way through has still refreshed the cards that were in the pool.
    """
    previous = previous or read_cards()
    known = list(previous)
    names = known + [n for n in get_card_names() if n not in previous]

    cards = {}
    pbar = tqdm(names)
    for name in pbar:
        pbar.set_description(name)
        image = get_card_image(name)
        if not image:
            # an action card, or a portrait the wiki has moved
            was = str(previous.get(name, {}).get('image', ''))
            if not was.startswith('http'):
                continue
            image = was
        cards[name] = {'name': name, 'image': image}
    return cards


def write_cards(cards: dict = None) -> dict:
    if cards is None:
        cards = get_cards()
    with open(cards_file, 'w', encoding='utf-8') as f:
        json.dump(cards, f, ensure_ascii=False, indent=2)
    return cards


if __name__ == '__main__':
    write_cards()
