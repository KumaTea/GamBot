from func.stickers.bro import *


def draw_text(text: str, font_path: str = FONT_PATH) -> Image:
    # initialize a transparent 100x100 image
    side_length = 100
    image = Image.new('RGBA', (side_length, side_length), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)

    # font_size = get_max_font_size(text, font_path, side_length, 5)
    font_size = 80
    font = ImageFont.truetype(font_path, font_size)
    text_width, text_height = get_textbox_size(text, font)

    # center the text
    # x = (100 - text_width) / 2
    # y = (100 - text_height) / 2
    if text.isalpha() or text.isdigit():
        x, y = 10, -5
    else:
        x, y = 20, -5
    draw.text((x, y), text, font=font, fill='white', stroke_width=2, stroke_fill='black')

    return image


def gen_chars(sentence: str):
    for index, char in enumerate(sentence):
        im = draw_text(char)
        filename = f'{str(index).zfill(3)}.png'
        im.save(f'data/stickers/{filename}')


# async def add_emoji(file):
#     print(file)
#     with open(file, 'rb') as f:
#         await me.send_document(429000, f)
#     await asyncio.sleep(1)
#     success = False
#     while not success:
#         try:
#             await me.send_message(429000, random.choice(EMOJIS))
#             success = True
#         except:
#             pass
#     await asyncio.sleep(2)

