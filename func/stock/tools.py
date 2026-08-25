from io import BytesIO
from time import time
from typing import Optional, Tuple
from share.common import no_preview
from telethon.tl.custom import Message
from telethon import TelegramClient as Client
from stock.main import query, stock_cache
from stock.tools import is_trading_time


def is_stale() -> bool:
    """
    Whether the cached index summary is worth showing again.

    Half a minute is nothing while the market is open and an eternity
    once it has closed, so the two cases get different patience.
    """
    now = int(time())
    age = now - stock_cache.last_timestamp
    trading = is_trading_time()
    return (
        (trading and age > 30) or
        age > 2 * 60 * 60 or
        trading != stock_cache.trading
    )


async def query_stock() -> Tuple[str, str, Optional[bytes]]:
    return await query(is_trading_time(), is_stale())


def as_image(content: bytes) -> Optional[BytesIO]:
    if not content:
        return None
    image = BytesIO(content)
    # Sina serves png for the mainland and gif elsewhere; Telegram works
    # the real type out for itself, the name is only a label
    image.name = 'stock.gif' if content[:3] == b'GIF' else 'stock.png'
    return image


async def send_stock(
        stock_summary: str,
        updown_bar: str = '',
        price_img: bytes = None,
        client: Client = None,
        chat_id: int = None,
        event=None
) -> Message:
    """The chart and the numbers, as one message when there is a chart."""
    assert (client and chat_id) or event
    text = f'{stock_summary}\n{updown_bar}' if updown_bar else stock_summary
    image = as_image(price_img)

    if event:
        if image:
            return await event.respond(text, file=image, **no_preview)
        return await event.respond(text, **no_preview)

    if image:
        return await client.send_message(chat_id, text, file=image, **no_preview)
    return await client.send_message(chat_id, text, **no_preview)
