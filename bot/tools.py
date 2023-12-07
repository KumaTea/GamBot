import re
from typing import Optional
from pyrogram.types import Message, User


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


def get_user_name(user: User):
    lang = user.language_code or 'zh'
    if user.last_name:
        if user.last_name.encode().isalpha() and user.first_name.encode().isalpha():
            space = ' '
        else:
            space = ''
        if 'zh' in lang:
            return f'{user.first_name}{space}{user.last_name}'
        else:
            return f'{user.first_name}{space}{user.last_name}'
    else:
        return user.first_name
