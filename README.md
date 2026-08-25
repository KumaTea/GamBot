# GamBot

A Telegram toy bot: a small casino, a paper-trading stock account, a
couple of gacha pools, and a picture collection. Built on Telethon.

## Commands

### 赌场

| Command | What it does |
| --- | --- |
| `/baccarat` `/bjl` `/百家乐` | 百家乐 — the whole group bets, buttons for type and amount |
| `/blackjack` `/bj` `/21点` | 21点 — one player against the dealer, hit / stand / double |
| `/slots` `/老虎机` | 老虎机 — `/slots 500`, three of a kind pays up to 120× |
| `/dice` `/骰宝` | 骰宝 — `/dice 大 500`, 豹子 pays 30:1 |
| `/games` `/赌场` | the list above, in the chat |

### 钱

Everything shares one balance, games and stock account alike.

| Command | What it does |
| --- | --- |
| `/balance` `/余额` | balance and leaderboard position |
| `/checkin` `/签到` | daily allowance, more for a streak |
| `/rank` `/富豪榜` | top ten |
| `/give` `/转账` | reply to someone with `/give 500` |

Anyone below the minimum balance is topped up at midnight.

### 股票

| Command | What it does |
| --- | --- |
| `/stock` | the three mainland indices, with the intraday chart |
| `/stock 600519` | one symbol — A shares, Hong Kong, US, and index aliases like `上证`, `恒生`, `纳指` |
| `/buy 600519 100` | buy, in lots of 100. `/buy 600519 all` spends what it can |
| `/sell 600519 100` | sell. `/sell 600519 all` closes the position |
| `/position` `/持仓` | holdings, cost, market value, profit |
| `/remind_stock` `/forget_stock` | ping me five minutes before the close |

Quotes come from Sina. Buying and selling is A shares only — the
balance is in yuan and there is no exchange rate to invent. Commission,
stamp duty and the transfer fee are charged the way a broker charges
them.

### 抽卡

`/gacha`, or `/gacha_ys` for 原神 and `/gacha_ak` for 明日方舟.

The pools live in `data/genshin/*.json` and `data/arknights/ops.json`.
Refresh them when a patch lands, or when the log complains that entries
have no picture:

```shell
python -m gacha.refresh              # both
python -m gacha.refresh genshin
python -m gacha.refresh arknights
```

原神 comes from the bilibili wiki; 明日方舟 comes from the game's own
data tables and artwork, both published on GitHub, so neither needs a
file prepared by hand. Nothing refreshes on a schedule.

### 存图

A named collection of pictures, filed by keyword and handed back at
random. `ruby` is the one that ships; more go in `collect/config.py`.

Anyone can ask for one:

```
/ruby
```

Only the accounts in `collect.config.ARCHIVISTS` can put one in. Any of
these files the picture:

- reply `/ruby` to a message with a picture in it
- send a picture captioned `ruby`
- reply `ruby` to a message with a picture in it
- say `ruby` right after a picture went past (yours or anyone's)
- send or forward a picture, or a direct image link, to the bot in private

`/ruby` only files when an archivist aims it at a picture. Pointed at
anything else — no reply, a reply to plain text, or anyone else asking —
it hands a picture out as usual.

**Page links cannot be filed** — an X post, say. Telegram hands bots
`webPageEmpty` for those and the methods that would resolve the preview
(`messages.getWebPagePreview`, `messages.getWebPage`) are both
`BOT_METHOD_INVALID`, for every URL, so there is nothing behind the link
a bot can reach. Forward the picture instead. Links that point straight
at an image file do work: the bot fetches it and hands it to Telegram
without sending it to anybody, so it still ends up with something
reusable.

**The keyword only works if the bot can see ordinary messages.** Turn
group privacy off in @BotFather (`/setprivacy` → Disable); with it on,
the bot only ever receives commands and has nothing to file.

### 其他

`/free` for this week's free games, `/bro` for a sticker.

## Running it

`config.ini`, next to `main.py`:

```ini
[jd]
api_id = ...
api_hash = ...
bot_token = ...
```

Then:

```shell
python main.py
```

Or in Docker, on `kumatea/telethon`:

```shell
docker build -t gambot -f docker/Dockerfile .
```

## Layout

Logic that does not know about Telegram lives at the top level —
`games/`, `stock/`, `gacha/`, `collect/`. The handlers that do live
under `func/`, and `handlers/register.py` wires the two together.

`share/` is a submodule shared with the other bots:

```shell
git submodule update --remote --merge share
```

State goes under `data/`, which is not tracked: balances and portfolios
as pickles, the picture collection as SQLite plus a blob directory, and
`data/media/cache.db` remembering which pictures Telegram already holds
so the same gacha art is not re-uploaded every time.
