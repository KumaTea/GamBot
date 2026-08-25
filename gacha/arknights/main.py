import json
import random
import logging


OPERATOR_DATA_FILE = 'data/arknights/ops.json'

gacha_rate = {
    1: 0.03,
    2: 0.04,
    3: 0.30,
    4: 0.35,
    5: 0.20,
    6: 0.08
}


def usable_images(entry: dict) -> list:
    """
    Every picture of an operator that can actually be sent.

    The old data mixes wiki urls with Bot API file ids left over from
    the pyrogram build; only the urls are any use now.
    """
    candidates = [entry.get('initial'), entry.get('promoted')]
    candidates += entry.get('skins') or []
    candidates += entry.get('others') or []
    return [i for i in candidates if str(i).startswith('http')]


class ArkData:
    def __init__(self):
        self.char = {}
        self.images = {}
        self.load()

    def load(self):
        with open(OPERATOR_DATA_FILE, 'r', encoding='utf-8') as f:
            everything = json.load(f)

        self.char = {}
        self.images = {}
        for name, entry in everything.items():
            if not entry:
                continue
            images = usable_images(entry)
            if not images:
                continue
            self.char[name] = entry
            self.images[name] = images

        missing = len(everything) - len(self.char)
        if missing:
            logging.warning(
                f'[gacha]\tarknights: {missing} of {len(everything)} operators have no '
                f'image url; run `python -m gacha.refresh arknights`')


ark_data = ArkData()

ops_by_rarity = {
    r: [name for name, e in ark_data.char.items() if e['rarity'] == r]
    for r in range(1, 7)
}


def char_select():
    pools = [r for r in gacha_rate if ops_by_rarity.get(r)]
    weights = [gacha_rate[r] for r in pools]
    rarity = random.choices(pools, weights=weights)[0]
    return random.choice(ops_by_rarity[rarity]), rarity


def gacha():
    char, rarity = char_select()
    return char, random.choice(ark_data.images[char]), rarity
