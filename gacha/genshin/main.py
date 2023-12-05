import json
import random


gacha_rate = {
    'boss': 0.1,
    'card': 0.1,
    'char': 0.7,
    'npc': 0.1
}

DATA_FILE = 'data/genshin/{DATA_TYPE}.json'
DATA_TYPES = list(gacha_rate.keys())


class GenshinData:
    def __init__(self):
        # self.boss = {}
        # self.card = {}
        # self.char = {}
        # self.npc = {}
        # for data_type in DATA_TYPES:
        #     setattr(self, data_type, {})
        self.load()

    def load(self):
        for data_type in DATA_TYPES:
            with open(DATA_FILE.format(DATA_TYPE=data_type), 'r', encoding='utf-8') as f:
                setattr(self, data_type, json.load(f))

    def save_img_id(self, data_type: str, name: str, img_id: str, key: str = 'image'):
        data = getattr(self, data_type)
        data[name][key] = img_id
        setattr(self, data_type, data)
        with open(DATA_FILE.format(DATA_TYPE=data_type), 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)


ys_data = GenshinData()

four_star = [i for i in ys_data.char if ys_data.char[i]['rarity'] == 4]
five_star = [i for i in ys_data.char if ys_data.char[i]['rarity'] == 5]
five_star_rate = 0.1


def type_select():
    types = list(gacha_rate.keys())
    weights = list(gacha_rate.values())
    return random.choices(types, weights=weights)[0]


def char_select():
    rarity = random.choices([4, 5], weights=[1-five_star_rate, five_star_rate])[0]
    if rarity == 4:
        char = random.choice(four_star)
    else:
        char = random.choice(five_star)
    char_img = ys_data.char[char]['image']
    return char, char_img, rarity


def gacha():
    gacha_type = type_select()
    if gacha_type == 'boss':
        name = random.choice(list(ys_data.boss.keys()))
        image = ys_data.boss[name]['image']
        type_str = '原魔'
    elif gacha_type == 'card':
        name = random.choice(list(ys_data.card.keys()))
        image = ys_data.card[name]['image']
        type_str = '七圣召唤卡牌'
    elif gacha_type == 'char':
        name, image, rarity = char_select()
        type_str = f'{rarity}星角色'
    else:
        name = random.choice(list(ys_data.npc.keys()))
        image = ys_data.npc[name]['image']
        type_str = 'NPC'
    return name, image, gacha_type, type_str
