from typing import Optional
from bot.media import message_image, pack_file_id
from telethon.tl.custom import Message
from common.info import administrators
from collect.config import PREVIEW_ACCOUNT
from func.collect.main import archive_preview, archive_private


async def private_message(event) -> Optional[Message]:
    """
    The bot's own chat, which only its owners are answered in.

    A picture or a link sent here is filed straight into a collection;
    anything else an admin sends a picture for gets its file id read
    back, which is handy when setting up static stickers and the like.
    """
    # The preview account is not somebody filing a picture -- it is
    # answering a link the bot asked it about, and its answer is the
    # picture. Taken first, or the branch below would read it a file id
    # back instead, which it has no use for.
    if event.sender_id == PREVIEW_ACCOUNT:
        return await archive_preview(event)

    if event.sender_id not in administrators:
        return None

    filed = await archive_private(event)
    if filed:
        return filed

    if message_image(event.message) is not None:
        return await reply_file_id(event)
    return None


async def reply_file_id(event) -> Message:
    """
    Telethon has no Bot API file id; report the packed legacy form when
    it can be built, and the raw media id otherwise.
    """
    file_id = pack_file_id(event.media)
    if file_id:
        return await event.reply(f'`{file_id}`')
    return await event.reply(f'`{message_image(event.message).id}`')
