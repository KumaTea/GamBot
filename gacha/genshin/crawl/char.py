import json
import requests
from tqdm import tqdm
from bs4 import BeautifulSoup


character_file = 'data/genshin/char.json'
character_url = 'https://wiki.biligame.com/ys/%E8%A7%92%E8%89%B2'
wiki_file_url = 'https://wiki.biligame.com/ys/%E6%96%87%E4%BB%B6:'


def get_character_list():
    r = requests.get(character_url)
    soup = BeautifulSoup(r.text, 'html.parser')
    char_links = soup.find_all('a')
    # must have a title attribute
    # char_links = [link for link in char_links if link.get('title')]
    # title value should equals to link text
    char_links = [link for link in char_links if link.get('title') == link.text]

    chars = [link.text for link in char_links]
    chars = list(set(chars))
    # known exception
    chars.remove('首页')
    # no twins
    for char in chars:
        if '旅行者' in char:
            chars.remove(char)
    # individual instead
    chars.append('空')
    chars.append('荧')
    return chars


def get_wiki_image_url(file):
    url = wiki_file_url + file
    r = requests.get(url)
    if r.status_code != 200:
        print('\nerror: ' + url)
        return ''
    soup = BeautifulSoup(r.text, 'html.parser')
    link = (
        soup.find('a', string='原始文件')  # 立绘
        or
        soup.find('a', string=file)  # 头像
    )
    if link:
        return link.get('href')
    else:
        print('\nerror: ' + url)
        return None


def get_character_head_image(char):
    file = '无背景-角色-' + char + '.png'
    return get_wiki_image_url(file)


def get_character_full_image(char):
    if char == '空':
        file = '旅行者立绘3.png'
    elif char == '荧':
        file = '旅行者立绘2.png'
    else:
        file = char + '立绘.png'
    return get_wiki_image_url(file)


def get_rarity_list():
    rarity_5 = []
    rarity_4 = []
    unknown = []
    chars = get_character_list()
    r = requests.get(character_url)
    soup = BeautifulSoup(r.text, 'html.parser')
    r5_divs = soup.find_all('div', class_='g C5星')
    r4_divs = soup.find_all('div', class_='g C4星')
    for char in chars:
        for div in r5_divs:
            if char in str(div):
                rarity_5.append(char)
                break
        for div in r4_divs:
            if char in str(div):
                rarity_4.append(char)
                break
    for char in chars:
        if char not in rarity_5 and char not in rarity_4:
            unknown.append(char)
    return rarity_5, rarity_4, unknown


def get_character_data():
    print('get character list')
    chars = get_character_list()
    print('get character rarity')
    rarity_5, rarity_4, unknown = get_rarity_list()

    char_data = {}
    print('get character image')
    pbar = tqdm(chars)
    for char in pbar:
        pbar.set_description(char)
        char_data[char] = {
            'name': char,
            'rarity': 5 if char in rarity_5 else 4 if char in rarity_4 else 0,
            'head': get_character_head_image(char),
            'image': get_character_full_image(char),
        }
        pbar.write(str(char_data[char]))
    return char_data


def write_character_data(char_data: dict = None):
    if char_data is None:
        char_data = get_character_data()
    with open(character_file, 'w', encoding='utf-8') as f:
        json.dump(char_data, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    write_character_data()
