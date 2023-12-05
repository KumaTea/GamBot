import random
from typing import List
from pyrogram.types import ChatMember


class GroupMembers:
    def __init__(self):
        self.groups = {}

    def update(self, chat_id: int, members: List[ChatMember]):
        self.groups[chat_id] = {
            'members': members
        }


grp_data = GroupMembers()


def gacha(chat_id: int) -> ChatMember:
    members = grp_data.groups[chat_id]['members']
    return random.choice(members)
