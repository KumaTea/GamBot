import os

if os.name != 'nt':
    import uvloop
    uvloop.install()

from bot.session import bot
from bot.starting import starting


starting()


if __name__ == '__main__':
    bot.run()
