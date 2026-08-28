import asyncio
import logging
from typing import Dict, Optional
from telethon.tl.custom import Message


RESULT_TTL = 5 * 60      # how long a finished answer stays on the wall

# Deleting our own message is always allowed. Deleting the command that
# asked for it needs an admin right the bot may not have, and there is
# no way to know which without trying -- so it is tried once per chat
# and the answer remembered. A chat that says no is never asked again.
_delete_rights: Dict[int, bool] = {}

# asyncio holds only a weak reference to a task, so one that nothing
# keeps can be collected before it runs, leaving the message forever
_pending: set = set()


async def take_back(message: Message, ours: bool = True) -> None:
    """Delete a message, learning once per chat whether that is allowed."""
    chat_id = message.chat_id
    if not ours and _delete_rights.get(chat_id) is False:
        return
    try:
        await message.delete()
        if not ours:
            _delete_rights[chat_id] = True
    except Exception as e:
        if not ours:
            _delete_rights[chat_id] = False
            logging.info(f'[fading]\tCannot delete others in {chat_id}, keeping commands: {e}')
        else:
            logging.warning(f'[fading]\tCould not take back {message.id}: {e}')


def fade(reply: Message, command: Optional[Message] = None, after: int = RESULT_TTL):
    """
    Take an answer off the wall once it has stopped being news.

    A group that plays a few rounds an hour is otherwise a wall of dead
    hands, and what a game settled is in the balance rather than in the
    message anyway. The command that asked goes at the same time, where
    the bot is allowed to delete it: half a conversation left behind
    reads worse than none of it.

    A restart in the meantime leaves both standing, which is not worth a
    scheduler to avoid -- they are clutter then, not a lie.
    """
    async def wait():
        await asyncio.sleep(after)
        await take_back(reply)
        if command is not None:
            await take_back(command, ours=False)

    task = asyncio.create_task(wait())
    _pending.add(task)
    task.add_done_callback(_pending.discard)


def transient(func):
    """
    Wrap a command so whatever it says clears up after itself.

    This goes on the command rather than on each message it edits,
    because a game hands back the one message it has been editing all
    along -- and because a complaint about the stake is as much clutter
    as a result is.
    """
    async def wrapper(event):
        reply = await func(event)
        if isinstance(reply, Message):
            fade(reply, getattr(event, 'message', None))
        return reply
    return wrapper
