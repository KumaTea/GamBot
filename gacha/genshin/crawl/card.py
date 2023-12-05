import json
import requests
from bs4 import BeautifulSoup


cards_file = r'data/genshin/card.json'
cards_url = 'https://wiki.biligame.com/ys/%E5%8D%A1%E7%89%8C%E4%B8%80%E8%A7%88'


def get_cards():
    cards = {}
    r = requests.get(cards_url)
    s = BeautifulSoup(r.text, 'html.parser')

    img_tags = s.find_all('img')
    for img in img_tags:
        alt = img.get('alt')
        if alt and '卡牌-角色牌' in alt:
            name = alt.split('-')[-1].replace('.png', '')
            image_url = img.get('src')
            cards[name] = {
                'name': name,
                'image': image_url
            }
    return cards


if __name__ == '__main__':
    c = get_cards()
    with open(cards_file, 'w', encoding='utf-8') as f:
        json.dump(c, f, ensure_ascii=False, indent=2)
