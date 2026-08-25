import os


if os.name == 'nt':
    # the repo root, wherever it has been checked out
    pwd = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
else:
    pwd = '/home/kuma/bots/jd'

# stock

SINA_HEADER = {
    'Referer': 'https://finance.sina.com.cn/realstock/company/sh000001/nc.shtml'
}

STOCK_PRICE_API = 'https://hq.sinajs.cn/list={STOCK_CODE}'

STOCK_PRICE_IMG = 'https://image.sinajs.cn/n/cn/min/640x360xxfhd/{STOCK_CODE}.png'
STOCK_PRICE_IMG_HK = 'https://image.sinajs.cn/newchart/hk_stock/min/{STOCK_CODE}.gif'
STOCK_PRICE_IMG_US = 'https://image.sinajs.cn/newchart/usstock/min/{STOCK_CODE}.gif'
# daily: https://image.sinajs.cn/newchart/daily/n/sh000001.gif
# weekly: https://image.sinajs.cn/newchart/weekly/n/sh000001.gif
# monthly: https://image.sinajs.cn/newchart/monthly/n/sh000001.gif
# backup: https://webquotepic.eastmoney.com/GetPic.aspx?imageType=r&nid=1.000001

UPDOWN_API = 'https://hq.sinajs.cn/list=sh000002_zdp,sz399107_zdp,sh000003_zdp,sz399108_zdp,sz399102_zdp'
UP_ICON = '🔴'
DOWN_ICON = '🟢'
STILL_ICON = '⚪'
RISE_ICON = '🔼'
FALL_ICON = '🔽'

STOCK_DATA_DIR = 'data/stock'
STOCK_REMINDER_FILE = 'reminder.p'
STOCK_PORTFOLIO_FILE = 'portfolio.p'

SH_URL = 'https://quote.eastmoney.com/zs000001.html'
SZ_URL = 'https://quote.eastmoney.com/zs399001.html'
CYB_URL = 'https://quote.eastmoney.com/zs399006.html'

# gacha

# # genshin
GACHA_GENSHIN_CMD = {'genshin', 'yuanshen', '原神', 'gs', 'ys', 'gi'}

# # arknights
GACHA_ARKNIGHTS_CMD = {'arknights', '方舟', '明日方舟', 'ark', 'mrfz', 'fz'}

# games

BACCARAT_RULE = 'https://zh.wikipedia.org/wiki/%E7%99%BE%E5%AE%B6%E6%A8%82#%E8%A3%9C%E7%89%8C%E8%A6%8F%E5%89%87'

TEASPS_ID = -1001932978232
