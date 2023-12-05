import aiohttp
from io import BytesIO


async def get_image(url: str) -> BytesIO:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            img_content = await resp.read()
    img_bytes = BytesIO(img_content)
    # img_bytes.seek(0)
    img_bytes.name = 'image.png'
    return img_bytes
