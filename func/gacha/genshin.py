from pyrogram import Client
from pyrogram.types import Message
from gacha.genshin.main import ys_data, gacha


async def gacha_genshin(client: Client, message: Message) -> Message:
    name, image, gacha_type, type_str = gacha()
    msg_text = f'恭喜你抽中了原神 {type_str} **{name}**！'
    reply = await message.reply_photo(
        photo=image,
        quote=False,
        caption=msg_text
    )
    if 'http' in image:
        img_id = reply.photo.file_id
        ys_data.save_img_id(
            data_type=gacha_type,
            name=name,
            img_id=img_id
        )
    return reply
