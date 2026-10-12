from typing import Optional
from dataclasses import dataclass
from common.info import creator


@dataclass(frozen=True)
class Collection:
    """
    One named pile of pictures.

    `commands` both hand a random picture back out and, replied to a
    picture by an archivist, file it. Adding a second pile is a matter
    of adding a second entry here.
    """
    name: str
    label: str
    commands: tuple[str, ...]
    empty_text: str = '还没有存过图片。'


COLLECTIONS: dict[str, Collection] = {
    'ruby': Collection(
        name='ruby',
        label='Ruby',
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

# Written anywhere in a picture sent to the bot in private, this keeps
# it from being filed -- the bot reads its file id back instead.
NO_ARCHIVE = '#noarchive'

# `/ruby <word>`, for an archivist. Anything else after the command is
# ignored, and everyone else just gets a picture as usual.
DELETE_WORDS = ('delete', 'del', 'rm', 'remove', '删除')


def all_commands() -> list[str]:
    return [cmd for c in COLLECTIONS.values() for cmd in c.commands]
