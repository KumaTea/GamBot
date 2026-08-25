import math
from share.auth import ensure_auth
from telethon.tl.custom import Message
from func.stickers.tools import to_webp
from func.stickers.bro import draw_text as draw_bro
from telethon.tl.types import InputStickerSetEmpty, DocumentAttributeSticker


# a .webp document only shows up as a sticker if it says so
STICKER_ATTRS = [DocumentAttributeSticker(alt='', stickerset=InputStickerSetEmpty())]


def get_text_length(text: str) -> int:
    try:
        return math.ceil(len(text.encode('gbk')) / 2)
    except UnicodeEncodeError:
        return len(text)


async def send_bro(event, sticker_text: str, reply=None) -> Message:
    sticker = to_webp(draw_bro(sticker_text))
    send = reply.reply if reply else event.respond
    return await send(file=sticker, attributes=STICKER_ATTRS, force_document=True)


@ensure_auth
async def command_bro(event) -> Message:
    command = event.raw_text
    content_index = command.find(' ')
    starting = '兄弟，'
    max_length = 5

    reply = await event.get_reply_message()
    if content_index == -1:
        # no text
        # /bro
        return await send_bro(event, f'{starting}你没写字')

    # has text
    # /bro example
    content = command[content_index + 1:]
    if get_text_length(content) > max_length:
        return await send_bro(event, f'{starting}最多五个字')
    return await send_bro(event, f'{starting}{content}', reply)
