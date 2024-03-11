from PIL import Image
from uuid import uuid4
from io import BytesIO


def to_webp(im: Image) -> BytesIO:
    webp = BytesIO()
    webp.name = f'{uuid4()}.webp'
    im.save(webp, 'webp')
    webp.seek(0)
    return webp
