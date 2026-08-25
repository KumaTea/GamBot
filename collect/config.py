from dataclasses import dataclass
from common.info import creator


@dataclass(frozen=True)
class Collection:
    """
    One named pile of pictures.

    `keywords` are what turns a message into a filing instruction, and
    `commands` are what hands a random picture back out again. Adding a
    second pile is a matter of adding a second entry here.
    """
    name: str
    label: str
    keywords: tuple[str, ...]
    commands: tuple[str, ...]
    empty_text: str = '还没有存过图片。'


COLLECTIONS: dict[str, Collection] = {
    'ruby': Collection(
        name='ruby',
        label='Ruby',
        keywords=('ruby',),
        commands=('ruby',),
        empty_text='Ruby 的相册还是空的。',
    ),
}


# Anyone may ask for a picture; only these accounts may put one in.
ARCHIVISTS: set[int] = {creator}

# How far back a bare keyword ("ruby and me") will look for the picture
# it refers to, when the message does not quote one itself.
RECENT_MEDIA_KEEP = 8          # messages remembered per chat
RECENT_MEDIA_TTL = 60 * 60     # seconds one stays worth filing


def collection_of_keyword(text: str) -> list[Collection]:
    """Every collection whose keyword appears in a piece of text."""
    lowered = (text or '').lower()
    return [c for c in COLLECTIONS.values() if any(k in lowered for k in c.keywords)]


def all_commands() -> list[str]:
    return [cmd for c in COLLECTIONS.values() for cmd in c.commands]
