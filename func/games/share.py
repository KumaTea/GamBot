import logging
from typing import Optional
from contextlib import asynccontextmanager
from share.common import message_link, no_preview
from telethon.errors import MessageNotModifiedError


class GameStatus:
    """
    Which chat is in the middle of what.

    One game per chat: two tables running at once in the same group is
    unreadable, and the cards would interleave.
    """
    def __init__(self):
        self.groups = {}

    def busy(self, chat_id: int) -> Optional[dict]:
        return self.groups.get(chat_id)

    def set_in_game(self, chat_id: int, game: str, msg_id: int = 1):
        self.groups[chat_id] = {'game': game, 'msg_id': msg_id}

    def set_message(self, chat_id: int, msg_id: int):
        if chat_id in self.groups:
            self.groups[chat_id]['msg_id'] = msg_id

    def game_over(self, chat_id: int):
        self.groups.pop(chat_id, None)


game_status = GameStatus()


async def busy_notice(event) -> Optional[str]:
    """What to tell someone who wants a table that is already in use."""
    running = game_status.busy(event.chat_id)
    if not running:
        return None
    chat = await event.get_chat()
    link = message_link(chat, running['msg_id'])
    return f'本群正在玩{running["game"]}，[这局]({link})结束后才能开始！'


@asynccontextmanager
async def table(event, game: str):
    """
    Hold the chat's one table for the length of a game.

    The `finally` is the point: a game that blows up half way through
    used to leave the group unable to start another one.
    """
    game_status.set_in_game(event.chat_id, game)
    try:
        yield
    finally:
        game_status.game_over(event.chat_id)


async def edit_text(message, text: str, buttons=None):
    """
    Edit, tolerating the one thing Telegram says about a no-op edit.

    Both the countdown and the buttons rewrite the same message, so
    landing on identical text is normal rather than a problem.
    """
    try:
        return await message.edit(text, buttons=buttons, **no_preview)
    except MessageNotModifiedError:
        return message
    except Exception as e:
        logging.warning(f'[games]\tCould not edit message: {e}')
        return message
