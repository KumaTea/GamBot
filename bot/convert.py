from PIL import Image
from io import BytesIO


def to_jpg(original_bytes: BytesIO) -> BytesIO:
    if isinstance(original_bytes, str):
        original_bytes = BytesIO(original_bytes.encode())
    elif isinstance(original_bytes, bytes):
        original_bytes = BytesIO(original_bytes)
    original_image = Image.open(original_bytes)
    # original_image.seek(0)
    image = original_image.convert('RGB')
    image_bytes = BytesIO()
    image_bytes.name = 'image.jpg'
    image.save(image_bytes, format='JPEG')
    # image_bytes.seek(0)
    return image_bytes
