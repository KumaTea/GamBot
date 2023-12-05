import json
import random


operator_data_file = 'data/arknights/ops.json'


class ArkData:
    def __init__(self):
        self.char = {}
        self.load()

    def load(self):
        with open(operator_data_file, 'r', encoding='utf-8') as f:
            self.char = json.load(f)

    def save_img_id(self, name: str, url: str, img_id: str):
        data = self.char[name]
        if data['initial'] == url:
            data['initial'] = img_id
        elif data['promoted'] == url:
            data['promoted'] = img_id
        else:
            for i in range(len(data['skins'])):
                if data['skins'][i] == url:
                    data['skins'][i] = img_id
                    break
        self.char[name] = data
        with open(operator_data_file, 'w', encoding='utf-8') as f:
            json.dump(self.char, f, ensure_ascii=False, indent=2)


ark_data = ArkData()

ops_by_rarity = {}
for r in range(1, 7):
    ops_by_rarity[r] = [name for name in ark_data.char if ark_data.char[name]['rarity'] == r]

gacha_rate = {
    1: 0.03,
    2: 0.04,
    3: 0.30,
    4: 0.35,
    5: 0.20,
    6: 0.08
}


def char_select():
    rarity = random.choices(list(gacha_rate.keys()), weights=list(gacha_rate.values()))[0]
    char = random.choice(ops_by_rarity[rarity])
    return char, rarity


def gacha():
    char, rarity = char_select()
    char_data = ark_data.char[char]
    images = [char_data['initial']]
    if char_data['promoted']:
        images.append(char_data['promoted'])
    images.extend(char_data['skins'])
    image = random.choice(images)
    return char, image, rarity
