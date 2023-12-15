import os
import json
import requests
from bs4 import BeautifulSoup
from gacha.genshin.crawl.char import get_wiki_image_url


boss_file = r'data/genshin/boss.json'


def get_image(name: str) -> str:
    img_url = get_wiki_image_url(name + '立绘.png')
    if not img_url:
        img_url = get_wiki_image_url(name + '.png')
    return img_url


def get_saved_boss_info() -> dict:
    if os.path.isfile(boss_file):
        with open(boss_file, 'r', encoding='utf-8') as f:
            saved_boss_info = json.load(f)
    else:
        saved_boss_info = {}
    return saved_boss_info


def get_wiki_page_name(html: str) -> str:
    s = BeautifulSoup(html, 'html.parser')
    name_div = s.find('meta', attrs={'property': 'og:title'})
    name = name_div.get('content')
    return name


def add_boss_info(url) -> dict:
    if 'http' not in url:
        url = 'https://wiki.biligame.com/ys/' + url
    r = requests.get(url)

    name = get_wiki_page_name(r.text)
    image_url = get_image(name)

    info = {
        'name': name,
        'image': image_url
    }
    return info


def save_boss_info(all_boss_info: dict) -> None:
    with open(boss_file, 'w', encoding='utf-8') as f:
        json.dump(all_boss_info, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    saved_boss = get_saved_boss_info()
    while u := input('URL: '):
        boss_info = add_boss_info(u)
        print(boss_info['name'], boss_info['image'])
        saved_boss[boss_info['name']] = boss_info
    save_boss_info(saved_boss)
