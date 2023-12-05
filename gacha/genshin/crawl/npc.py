import os
import json
import requests
from bs4 import BeautifulSoup
from gacha.genshin.crawl.char import get_wiki_image_url


npc_file = r'data/genshin/npc.json'


def get_saved_npc_info() -> dict:
    if os.path.isfile(npc_file):
        with open(npc_file, 'r', encoding='utf-8') as f:
            saved_npc_info = json.load(f)
    else:
        saved_npc_info = {}
    return saved_npc_info


def name_detect(html: str) -> str:
    s = BeautifulSoup(html, 'html.parser')
    name_div = s.find('div', class_='npcName')
    name = name_div.text.strip()
    return name


def location_detect(html: str) -> str:
    if 'npcAddress npcAddress蒙德' in html:
        return '蒙德'
    elif 'npcAddress npcAddress璃月' in html:
        return '璃月'
    elif 'npcAddress npcAddress稻妻' in html:
        return '稻妻'
    elif 'npcAddress npcAddress须弥' in html:
        return '须弥'
    elif 'npcAddress npcAddress枫丹' in html:
        return '枫丹'
    elif 'npcAddress npcAddress纳塔' in html:
        return '纳塔'
    elif 'npcAddress npcAddress至东' in html:
        return '至东'
    return '？？'


def image_detect(html: str) -> str:
    css_start = '.npcAllicon'
    img_url_start = 'background-image:url('
    img_url_end = ')'

    img_url = ''
    if css_start in html:
        css_start_index = html.find(css_start)
        img_url_start_index = html.find(img_url_start, css_start_index)
        img_url_end_index = html.find(img_url_end, img_url_start_index)
        img_url = html[img_url_start_index+len(img_url_start):img_url_end_index]

    if not img_url:
        name = name_detect(html)
        img_url = get_wiki_image_url(name + '.png')

    return img_url


def add_npc_info(url) -> dict:
    r = requests.get(url)

    name = name_detect(r.text)
    location = location_detect(r.text)
    image_url = image_detect(r.text)

    npc_info = {
        'name': name,
        'location': location,
        'image': image_url
    }
    return npc_info


def save_npc_info(all_npc_info: dict) -> None:
    with open(npc_file, 'w', encoding='utf-8') as f:
        json.dump(all_npc_info, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    saved_npc = get_saved_npc_info()
    while u := input('URL: '):
        npc_info = add_npc_info(u)
        print(npc_info['name'], npc_info['location'], npc_info['image'])
        saved_npc[npc_info['name']] = npc_info
    save_npc_info(saved_npc)
