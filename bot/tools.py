import re
from typing import Optional
from pyrogram.types import Message


cmd_pattern = re.compile(r'^/\w+@?\w+[\s\n]')


def get_command_content(message: Message) -> Optional[str]:
    """
    Remove /cmd of a message,
    or get its replied message.
    Message must start with '/'.
    """
    text = message.text
    if not text:
        return None

    match = cmd_pattern.match(text)
    if match:
        return text[match.end():]
    return None
