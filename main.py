import os
import asyncio

if os.name != 'nt':
    try:
        import uvloop
        uvloop.install()
    except ImportError:
        # a nicety, not a requirement
        pass

from bot.starting import starting
from bot.session import bot, BOT_TOKEN


async def main():
    await bot.start(bot_token=BOT_TOKEN)
    starting()
    await bot.run_until_disconnected()


if __name__ == '__main__':
    asyncio.run(main())
