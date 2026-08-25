"""
Rebuild the operator pool from the game's own data.

The old version scraped prts.wiki and needed a hand-maintained csv of
operator names to start from. Both of those are gone: the game data and
the artwork are published as plain files, so a refresh is now one run
with nothing to prepare.
"""
import json
import requests
from tqdm import tqdm
from urllib.parse import quote
from collections import defaultdict
from share.data import USER_AGENT


operator_data_file = 'data/arknights/ops.json'

GAME_DATA = ('https://raw.githubusercontent.com/Kengxxiao/ArknightsGameData'
             '/master/zh_CN/gamedata/excel/{table}.json')
PORTRAIT = ('https://raw.githubusercontent.com/yuanyan3060/ArknightsGameResource'
            '/main/portrait/{portrait}.png')

HEADERS = {'User-Agent': USER_AGENT}
TIMEOUT = 60

PROFESSIONS = {
    'PIONEER': '先锋',
    'WARRIOR': '近卫',
    'SNIPER': '狙击',
    'TANK': '重装',
    'MEDIC': '医疗',
    'SUPPORT': '辅助',
    'CASTER': '术师',
    'SPECIAL': '特种',
}

RARITY_TIERS = {f'TIER_{n}': n for n in range(1, 7)}


def fetch(table: str) -> dict:
    r = requests.get(GAME_DATA.format(table=table), headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def portrait_url(portrait_id: str) -> str:
    """Skin ids carry `#` and `+`, which a url will not take unescaped."""
    return PORTRAIT.format(portrait=quote(portrait_id, safe=''))


def rarity_of(entry: dict) -> int:
    rarity = entry.get('rarity')
    if isinstance(rarity, int):
        # the table used to store a zero-based index
        return rarity + 1
    return RARITY_TIERS.get(rarity, 1)


def is_operator(char_id: str, entry: dict) -> bool:
    """
    Operators, as opposed to enemies, summons and trap devices.

    They live in the same table, and the ones a player can actually own
    are the ones with a handbook number that are still obtainable.
    """
    return bool(
        char_id.startswith('char_') and
        entry.get('displayNumber') and
        not entry.get('isNotObtainable')
    )


def portraits_by_char(skins: dict) -> dict:
    """
    Every portrait of every operator, base art first.

    `_1` is the operator as recruited and `_2` is the elite two artwork;
    everything else is a skin, and the order among those does not matter.
    """
    by_char = defaultdict(list)
    for skin in skins.values():
        char_id = skin.get('charId')
        portrait_id = skin.get('portraitId')
        if char_id and portrait_id:
            by_char[char_id].append(portrait_id)

    for char_id, ids in by_char.items():
        by_char[char_id] = sorted(ids, key=lambda p: (
            0 if p.endswith('_1') else 1 if p.endswith('_2') else 2, p))
    return by_char


def build_ops() -> dict:
    print('fetching game data...')
    characters = fetch('character_table')
    skins = fetch('skin_table')['charSkins']
    branches = fetch('uniequip_table')['subProfDict']
    powers = fetch('handbook_team_table')

    art = portraits_by_char(skins)
    ops = {}

    for char_id, entry in tqdm(characters.items()):
        if not is_operator(char_id, entry):
            continue

        portraits = art.get(char_id) or []
        urls = [portrait_url(p) for p in portraits]
        group_id = entry.get('nationId') or entry.get('groupId') or entry.get('teamId')
        branch = branches.get(entry.get('subProfessionId'), {})
        approach = entry.get('itemObtainApproach')

        ops[entry['name']] = {
            'name': entry['name'],
            'rarity': rarity_of(entry),
            'group': (powers.get(group_id) or {}).get('powerName', ''),
            'class': PROFESSIONS.get(entry.get('profession'), ''),
            'branch': branch.get('subProfessionName', ''),
            'initial': urls[0] if urls else '',
            'promoted': urls[1] if len(urls) > 1 else '',
            'skins': urls[2:],
            'approach': [approach] if approach else [],
            'others': [],
        }
    return ops


def save_ops_query_data(ops: dict):
    with open(operator_data_file, 'w', encoding='utf-8') as f:
        json.dump(ops, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    save_ops_query_data(build_ops())
