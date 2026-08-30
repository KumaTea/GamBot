from typing import Optional
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
        keywords=('ruby', '路比'),
        commands=('ruby',),
        empty_text='Ruby 的相册还是空的。',
    ),
}


# Anyone may ask for a picture; only these accounts may put one in.
ARCHIVISTS: set[int] = {creator}

# The account that can see what is behind a page link.
#
# Telegram renders link previews for people and not for bots: a bot is
# handed `webPageEmpty` for every page link, and both of the methods
# that would resolve one -- `messages.getWebPagePreview` and
# `messages.getWebPage` -- answer it BOT_METHOD_INVALID. So a page link
# goes to a user account running `preview.py`, which sends the picture
# back as an ordinary message. None when nothing is running there, in
# which case page links are simply not filable, the way they were before.
PREVIEW_ACCOUNT: Optional[int] = 345060487

# Which pile a picture belongs to when nothing says otherwise -- notably
# one that comes back from the preview account, which answers a link
# rather than a request and so has no collection attached to it.
DEFAULT_COLLECTION = 'ruby'

# How far back a bare keyword ("ruby and me") will look for the picture
# it refers to, when the message does not quote one itself.
#
# Counted in messages from the same person: another bot talking in
# between uses none of it up, because everybody is remembered apart.
RECENT_KEEP = 3                # messages remembered per person, per chat
RECENT_TTL = 60 * 60           # seconds one stays worth filing

# Written anywhere in a message, this keeps the bot's hands off it: the
# message files nothing and is not remembered for a later keyword to
# point back at. Aiming `/ruby` at something is still deliberate, and
# still files it.
NO_ARCHIVE = '#noarchive'

# `/ruby <word>`, for an archivist. Anything else after the command is
# ignored, and everyone else just gets a picture as usual.
RESET_WORDS = ('reset', 'forget', '忘记')
DELETE_WORDS = ('delete', 'del', 'rm', 'remove', '删除')


def collection_of_keyword(text: str) -> list[Collection]:
    """Every collection whose keyword appears in a piece of text."""
    lowered = (text or '').lower()
    return [c for c in COLLECTIONS.values() if any(k in lowered for k in c.keywords)]


def all_commands() -> list[str]:
    return [cmd for c in COLLECTIONS.values() for cmd in c.commands]
