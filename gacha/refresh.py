"""
Refill the gacha pools from the wikis and the game's own data.

Run it when a pool has gone stale -- after a new patch, or after the
warning about entries with no image url shows up in the log:

    python -m gacha.refresh              # everything
    python -m gacha.refresh genshin
    python -m gacha.refresh arknights

Nothing here runs on a schedule. The pools are a few hundred pictures
that change a handful of times a year, and a refresh that only happens
when someone asks for it cannot quietly break in the background.
"""
import sys
import json
import logging
from tqdm import tqdm


def keep_url(new: str, old: str) -> str:
    """A fresh url wins; a missing one leaves whatever worked before."""
    if new:
        return new
    return old if str(old).startswith('http') else ''


def refresh_genshin_chars():
    from gacha.genshin.crawl.char import (
        get_character_data, read_character_data, write_character_data)
    print('genshin: characters')
    data = write_character_data(get_character_data(read_character_data()))
    report('genshin/char', data)


def refresh_genshin_cards():
    from gacha.genshin.crawl.card import get_cards, write_cards
    print('genshin: cards')
    report('genshin/card', write_cards(get_cards()))


def refresh_genshin_named(kind: str):
    """
    Bosses and NPCs, whose entries were added by hand one url at a time.

    The names are already on file; only the pictures go stale, and those
    can be looked up from the name alone.
    """
    from gacha.genshin.crawl.char import get_wiki_image_url
    print(f'genshin: {kind}')

    path = f'data/genshin/{kind}.json'
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        logging.warning(f'no {path} to refresh: {e}')
        return

    for name, entry in tqdm(list(data.items())):
        found = get_wiki_image_url(f'{name}立绘.png') or get_wiki_image_url(f'{name}.png')
        entry['image'] = keep_url(found, entry.get('image', ''))

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    report(f'genshin/{kind}', data)


def refresh_arknights():
    from gacha.arknights.crawl.main import build_ops, save_ops_query_data
    print('arknights: operators')
    ops = build_ops()
    save_ops_query_data(ops)
    report('arknights', ops, image_keys=('initial', 'promoted'))


def report(pool: str, data: dict, image_keys=('image',)):
    def has_image(entry: dict) -> bool:
        if not entry:
            return False
        candidates = [entry.get(k) for k in image_keys]
        candidates += entry.get('skins') or []
        return any(str(c).startswith('http') for c in candidates)

    usable = sum(1 for e in data.values() if has_image(e))
    print(f'  {pool}: {usable} of {len(data)} have pictures')


def refresh_genshin():
    refresh_genshin_chars()
    refresh_genshin_cards()
    refresh_genshin_named('boss')
    refresh_genshin_named('npc')


TARGETS = {
    'genshin': refresh_genshin,
    'arknights': refresh_arknights,
}


def main(argv: list):
    wanted = argv or list(TARGETS)
    unknown = [name for name in wanted if name not in TARGETS]
    if unknown:
        print(f'unknown pool: {", ".join(unknown)}')
        print(f'try one of: {", ".join(TARGETS)}')
        return 1

    for name in wanted:
        TARGETS[name]()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
