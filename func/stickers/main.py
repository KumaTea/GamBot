import math
from pyrogram import Client
from share.auth import ensure_auth
from pyrogram.types import Message
from func.stickers.tools import to_webp
from common.data import BRO_EMPTY, BRO_TOO_LONG
from func.stickers.bro import draw_text as draw_bro


def get_text_length(text: str) -> int:
    try:
        return math.ceil(len(text.encode('gbk')) / 2)
    except UnicodeEncodeError:
        return len(text)


@ensure_auth
async def command_bro(client: Client, message: Message) -> Message:
    command = message.text
    content_index = command.find(' ')
    starting = '兄弟，'
    max_length = 5

    reply = message.reply_to_message
    if content_index == -1:
        # no text
        # /bro
        # sticker_text = f'{starting}你没写字'
        # sticker = draw_bro(sticker_text)
        resp = await message.reply_sticker(BRO_EMPTY, quote=False)
    else:
        # has text
        # /bro example
        content = command[content_index+1:]
        if get_text_length(content) > max_length:
            # sticker_text = f'{starting}最多五个字'
            # sticker = draw_bro(sticker_text)
            resp = await message.reply_sticker(BRO_TOO_LONG, quote=False)
        else:
            sticker_text = f'{starting}{content}'
            sticker = draw_bro(sticker_text)
            if reply:
                resp = await reply.reply_sticker(to_webp(sticker))
            else:
                resp = await message.reply_sticker(to_webp(sticker), quote=False)
    # logging.info(f'[bro] {sticker_text=}\t{resp.sticker.file_id=}')
    return resp
