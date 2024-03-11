from common.data import pwd
from PIL import Image, ImageDraw, ImageFont


TEMPLATE = f'{pwd}/data/stickers/bro.png'
SIDE_LENGTH = 400
SPACING = 20
FONT_PATH = f'{pwd}/data/stickers/msyh.ttc'


def get_textbox_size(text: str, font: ImageFont) -> tuple:
    textbox = font.getbbox(text)
    x0, y0, x1, y1 = textbox
    return x1 - x0, y1 - y0


def get_max_font_size(
        text: str,
        font_path: str = FONT_PATH,
        side_length: int = SIDE_LENGTH,
        spacing: int = SPACING
) -> int:
    font_size = 1
    font = ImageFont.truetype(font_path, font_size)
    text_width, text_height = get_textbox_size(text, font)

    while (text_width < (side_length - 2 * spacing)) and (text_height < (side_length - 2 * spacing)):
        font_size += 1
        font = ImageFont.truetype(font_path, font_size)
        text_width, text_height = get_textbox_size(text, font)

    # now text_width >= SIDE_LENGTH - SPACING
    return font_size - 1


def draw_text(text: str, font_path: str = FONT_PATH) -> Image:
    image = Image.open(TEMPLATE)
    draw = ImageDraw.Draw(image)
    image_width = SIDE_LENGTH

    font_size = get_max_font_size(text, font_path)
    font = ImageFont.truetype(font_path, font_size)
    text_width, text_height = get_textbox_size(text, font)

    # top, center
    x = (image_width - text_width) / 2
    y = 0
    draw.text((x, y), text, font=font, fill='black')

    return image
