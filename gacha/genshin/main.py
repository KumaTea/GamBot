import json
import random
import logging


gacha_rate = {
    'boss': 0.1,
    'card': 0.1,
    'char': 0.7,
    'npc': 0.1
}

DATA_FILE = 'data/genshin/{DATA_TYPE}.json'
DATA_TYPES = list(gacha_rate.keys())

FIVE_STAR_RATE = 0.1


def has_image(entry: dict) -> bool:
    """
    A pool entry worth rolling.

    Entries whose `image` is one of the old Bot API file ids are dead
    weight -- Telethon cannot send those -- so they stay out of the pool
    until a refresh gives them a real url.
    """
    return str(entry.get('image', '')).startswith('http')


class GenshinData:
    def __init__(self):
        self.load()

    def load(self):
        for data_type in DATA_TYPES:
            with open(DATA_FILE.format(DATA_TYPE=data_type), 'r', encoding='utf-8') as f:
                everything = json.load(f)
            usable = {k: v for k, v in everything.items() if has_image(v)}
            missing = len(everything) - len(usable)
            if missing:
                logging.warning(
                    f'[gacha]\tgenshin/{data_type}: {missing} of {len(everything)} '
                    f'have no image url; run `python -m gacha.refresh genshin`')
            setattr(self, data_type, usable)


ys_data = GenshinData()

four_star = [i for i in ys_data.char if ys_data.char[i]['rarity'] == 4]
five_star = [i for i in ys_data.char if ys_data.char[i]['rarity'] == 5]


def type_select() -> str:
    """Only pools that still have something in them."""
    pools = [t for t in DATA_TYPES if getattr(ys_data, t)]
    weights = [gacha_rate[t] for t in pools]
    return random.choices(pools, weights=weights)[0]


def char_select():
    rarity = random.choices([4, 5], weights=[1 - FIVE_STAR_RATE, FIVE_STAR_RATE])[0]
    pool = five_star if rarity == 5 else four_star
    if not pool:
        pool = four_star or five_star
        rarity = 4 if pool is four_star else 5
    char = random.choice(pool)
    return char, ys_data.char[char]['image'], rarity


def gacha():
    gacha_type = type_select()
    if gacha_type == 'char':
        name, image, rarity = char_select()
        return name, image, gacha_type, f'{rarity}星角色'

    type_names = {'boss': '原魔', 'card': '七圣召唤卡牌', 'npc': 'NPC'}
    pool = getattr(ys_data, gacha_type)
    name = random.choice(list(pool))
    return name, pool[name]['image'], gacha_type, type_names[gacha_type]
