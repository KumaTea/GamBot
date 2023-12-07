import csv
import json
import requests
from tqdm import tqdm
from bs4 import BeautifulSoup


operator_file = 'data/arknights/op.csv'
header = 'sortId,name,rarity,approach,date'.split(',')
wiki_file_url = 'https://prts.wiki/w/%E6%96%87%E4%BB%B6:'
operator_data_file = 'data/arknights/ops.json'


def get_wiki_image(filename):
    url = wiki_file_url + filename
    r = requests.get(url)
    if r.status_code != 200:
        print('\nerror: ' + url)
        return ''
    soup = BeautifulSoup(r.text, 'html.parser')
    link = (
        soup.find('a', string='原始文件')  # 立绘
        or
        soup.find('a', string=filename)  # 头像
    )
    if link:
        href = link.get('href')
        full_url = 'https://prts.wiki' + href
        return full_url
    else:
        print('\nerror: ' + url)
        return None


def get_op_info(html):
    name_start = html.find('var char_info={"name":"')
    name_end = html.find('","nameEn":"', name_start)
    rarity_start = html.find('"star":', name_end)
    rarity_end = html.find(',"group":"', rarity_start)
    group_start = html.find('"group":"', rarity_end)
    group_end = html.find('","class":"', group_start)
    class_start = html.find('"class":"', group_end)
    class_end = html.find('","branch":"', class_start)
    branch_start = html.find('"branch":"', class_end)
    branch_end = html.find('","pos":"', branch_start)

    name = html[name_start + len('var char_info={"name":"'):name_end]
    rarity_index = html[rarity_start + len('"star":'):rarity_end]
    rarity = int(rarity_index) + 1
    group = html[group_start + len('"group":"'):group_end]
    op_class = html[class_start + len('"class":"'):class_end]
    branch = html[branch_start + len('"branch":"'):branch_end]

    return name, rarity, group, op_class, branch


def get_images(name: str):
    initial_name = f'立绘 {name} 1.png'
    promoted_name = f'立绘 {name} 2.png'

    skins = []
    initial = get_wiki_image(initial_name)
    promoted = get_wiki_image(promoted_name)
    for i in range(1, 10):
        skin_name = f'立绘 {name} skin{i}.png'
        skin = get_wiki_image(skin_name)
        if skin:
            skins.append(skin)
        else:
            break

    return initial, promoted, skins


def get_op_data(name: str):
    url = f'https://prts.wiki/w/{name}'
    r = requests.get(url)
    if r.status_code != 200:
        print('\nerror: ' + url)
        return None

    _, rarity, group, op_class, branch = get_op_info(r.text)
    initial, promoted, skins = get_images(name)

    data = {
        'name': name,
        'rarity': rarity,
        'group': group,
        'class': op_class,
        'branch': branch,
        'initial': initial,
        'promoted': promoted,
        'skins': skins,
        'others': []
    }
    return data


def read_op_csv():
    ops = {}
    with open(operator_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            sort_id, name, rarity_index, approaches, date = row
            ops[name] = {
                'sort_id': sort_id,
                'name': name,
                'rarity': int(rarity_index) + 1,
                'approach': approaches.split(),
                'date': date
            }
    return ops


def query_ops():
    ops_csv_data = read_op_csv()
    for op in ops_csv_data.copy():
        if int(ops_csv_data[op]['sort_id']) < 0:
            del ops_csv_data[op]

    ops = {}
    pbar = tqdm(ops_csv_data)
    for op in pbar:
        pbar.set_description(op)
        data = get_op_data(op)
        if data:
            data['approach'] = ops_csv_data[op]['approach']
        ops[op] = data
        # pbar.write(str(data))

    return ops


def save_ops_query_data(ops: dict):
    with open(operator_data_file, 'w', encoding='utf-8') as f:
        json.dump(ops, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    ops = query_ops()
    save_ops_query_data(ops)
