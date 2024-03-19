import os


if os.name == 'nt':
    pwd = r'D:\GitHub\GamBot'
else:
    pwd = '/home/kuma/bots/jd'

# common

PHOTO_COMMIT_MSG = 'commit user photo'

url_regex = r'https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|' \
            r'www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|' \
            r'https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|' \
            r'www\.[a-zA-Z0-9]+\.[^\s]{2,}'

# stock

SINA_HEADER = {
    'Referer': 'https://finance.sina.com.cn/realstock/company/sh000001/nc.shtml'
}

STOCK_PRICE_API = 'https://hq.sinajs.cn/list={STOCK_CODE}'

# STOCK_PRICE_IMG = 'https://image.sinajs.cn/newchart/min/n/{STOCK_CODE}.gif'
STOCK_PRICE_IMG = 'https://image.sinajs.cn/n/cn/min/640x360xxfhd/{STOCK_CODE}.png'
# daily: https://image.sinajs.cn/newchart/daily/n/sh000001.gif
# weekly: https://image.sinajs.cn/newchart/weekly/n/sh000001.gif
# monthly: https://image.sinajs.cn/newchart/monthly/n/sh000001.gif
# backup: https://webquotepic.eastmoney.com/GetPic.aspx?imageType=r&nid=1.000001
STOCK_PRICE_SMALL_IMG = 'https://image.sinajs.cn/newchart/hollow/small/nsh000001.gif'

UPDOWN_API = 'https://hq.sinajs.cn/list=sh000002_zdp,sz399107_zdp,sh000003_zdp,sz399108_zdp,sz399102_zdp'
UP_ICON = '🔴'
DOWN_ICON = '🟢'
STILL_ICON = '⚪'
RISE_ICON = '🔼'
FALL_ICON = '🔽'

STOCK_DATA_DIR = 'data/stock'
STOCK_REMINDER_FILE = 'reminder.p'

SH_URL = 'https://quote.eastmoney.com/zs000001.html'
SZ_URL = 'https://quote.eastmoney.com/zs399001.html'
CYB_URL = 'https://quote.eastmoney.com/zs399006.html'

# gacha

LOADING_DEFAULT = 'AgACAgUAAxkBAAMGZW8yOiTRz6gW2CvtXOn4eTqqit8AAi68MRvj_XlXULp0igotjbgACAEAAwIAA3gABx4E'

# # genshin
GACHA_GENSHIN_CMD = {'genshin', 'yuanshen', '原神', 'gs', 'ys', 'gi'}
LOADING_GENSHIN = 'AgACAgUAAxkBAAMIZW8yh3HdhNmpzgnc8nczPGZeeq8AApe7MRtbkHhXEJyXoUvTpHoACAEAAwIAA3kABx4E'

# # arknights
GACHA_ARKNIGHTS_CMD = {'arknights', '方舟', '明日方舟', 'ark', 'mrfz', 'fz'}
LOADING_ARKNIGHTS = 'AgACAgUAAxkBAAMKZW8yztd5Nux3qoyXotgaTjFapkgAApm7MRtbkHhXIHKInNaQDMoACAEAAwIAA3kABx4E'

# # groupmem
USER_PHOTO_DIR = 'data/groupmem'
USER_PHOTO_FILE = 'photo.p'
GACHA_GROUPMEM_CMD = {'groupmem', '群老婆', 'qlp', 'lp', 'group'}

# games

BACCARAT_RULE = 'https://zh.wikipedia.org/wiki/%E7%99%BE%E5%AE%B6%E6%A8%82#%E8%A3%9C%E7%89%8C%E8%A6%8F%E5%89%87'

# stickers

BRO_EMPTY = 'CAACAgUAAx0ESGhsZQACCRtl0PkJvFKwi9_y7hFc1fRUyRkZGwAClwwAAvuviVYYqNOATmN-nh4E'
BRO_TOO_LONG = 'CAACAgUAAx0ESGhsZQACCR1l0PkzUuWbdIzce1ZLe8SfBO6hFQACmAwAAvuviVb9wkBndh3lcR4E'

USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/122.0.0.0 '
    'Safari/537.36'
)

TEASPS_ID = -1001932978232
