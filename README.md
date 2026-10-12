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

A command with no amount on it bets 1000, or everything there is when
that is less than 1000 — a player with 300 left means the 300, and the
table minimum does not stand in the way of somebody's last chips.

**One game at a time, per player.** Four `/blackjack` in a row are four
games: they queue up and are played in order, each reading a balance the
one before it has finished writing. Asking for a fifth while four are in
flight gets a shrug rather than a place in the queue. Baccarat is not
queued — the whole group plays one hand together, and a chat already
holds a single table of its own.

**A finished game clears itself up after five minutes**, along with the
command that asked for it where the bot is allowed to delete other
people's messages. Whether it is allowed is asked once per chat and
remembered; a chat that says no is never asked again. Nothing is lost
with the message — the balance and the profit column are what a game
leaves behind.

### 钱

Everything shares one balance, games and stock account alike.

| Command | What it does |
| --- | --- |
| `/balance` `/余额` | balance, profit and loss, leaderboard position |
| `/checkin` `/签到` | daily allowance, more for a streak — fades like a game |
| `/rank` `/富豪榜` | top ten, and what the house is up |
| `/give` `/转账` | reply to someone with `/give 500` |

Anyone below the minimum balance is topped up at midnight.

**Profit and loss is what was won and lost at the tables**, which is not
the same as what somebody has. An allowance, a midnight top-up, a
transfer or a stock trade all move the balance without anybody having
won anything, so none of them go in the column: only a settled wager
does. The bank keeps a seat of its own holding the mirror image, so
every player's profit together with the house's comes to nothing.

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

`/gacha`, or `/gacha_ys` for 原神 and `/gacha_ak` for 明日方舟. A pull
clears itself up after five minutes, the same as a game does.

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

A named collection of pictures, handed back at random. `ruby` is the
one that ships; more go in `collect/config.py`.

Anyone can ask for one:

```
/ruby
```

Only the accounts in `collect.config.ARCHIVISTS` can put one in, and
there are two ways:

- reply `/ruby` to a message with a picture or a link in it
- send or forward a picture, or a link, to the bot in private

`/ruby` only files when an archivist aims it at a picture. Pointed at
anything else — no reply, a reply to plain text, or anyone else asking —
it hands a picture out as usual. Nothing else in a group files
anything: the word `ruby` in a sentence is just a word.

In private, `#NoArchive` in the caption keeps a picture out of the
collection; the bot reads its file id back instead.

Every filing says which row it became:

```
Ruby +1（#565，共 556 张）
```

`#565` is the id `/ruby delete` and `/ruby 565` take. The 556 next to it
is only a count — deleted rows leave gaps, so the two drift apart.

A link handed over this way is answered with 交给取图的账号了 — which
takes itself back after five minutes. The picture it promises turns up
under the message that asked for it, captioned with its id, once it is
filed: that is the moment to see that a page's preview was the wrong
picture, and to reply `/ruby delete` to it.

Where a picture came from is kept alongside it: the url of the preview
it was filed from, or a link in its caption when there was no preview.

#### Looking at one, taking one back out

For an archivist:

```
/ruby 42                # show #42, captioned with its id
/ruby delete            # replying to a picture the bot sent
/ruby delete 42         # by id, the # number from the filing report
/ruby delete https://…  # by the url it was filed from
```

Replying `/ruby delete` works on any picture the bot sent — a draw, a
`/ruby 42`, or the picture a link came back as.

The saved bytes go with the row, unless another collection still points
at them.

#### Editing the database by hand

`data/collect/collect.db` is plain SQLite and can be edited while the
bot runs, as long as it is edited in place — `sqlite3` on the server,
or sqlite-web pointed at it. Do not copy it off and back while the bot
is running: that puts a new file where the old one was, the bot keeps
the old one open, and every write after it fails as "attempt to write a
readonly database". If it has to be done that way, stop the bot first.

The picture column is a Telegram file reference and shows as a blob in
any viewer. `/ruby 42` is the way to see what a row is.

**Page links go through a second account** — an X post, say. Telegram
hands bots `webPageEmpty` for those, and the methods that would resolve
the preview (`messages.getWebPagePreview`, `messages.getWebPage`) are
both `BOT_METHOD_INVALID`, for every URL, so there is nothing behind
such a link a bot can reach on its own. A user account can see the
preview perfectly well, so one runs `preview.py` and does the looking:
the bot sends it the link and carries on, and the picture arrives a
moment later as an ordinary message, which is filed when it turns up.
Nothing is held open in between, so nothing can time out — and equally,
a link with no picture behind it is answered with silence.

Set `collect.config.PREVIEW_ACCOUNT` to `None` to turn that off; page
links are then a dead end again, and forwarding the picture is the way.

Links that point straight at an image file never needed any of it: the
bot fetches those itself and hands them to Telegram without sending
them to anybody, so it still ends up with something reusable.

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

### The preview account

`preview.py` is a second process and a second Telegram account, whose
whole job is described under 存图 above: it is sent a link and it sends
the picture back. It answers nothing else, and shares no state with the
bot — no `data/`, no database — so it can be started, stopped and
restarted on its own.

It reads the same `config.ini`, taking `[preview]` if that section is
there and falling back to `[jd]` for the api credentials, which a user
session may share with the bot:

```ini
[preview]
api_id = ...
api_hash = ...
session = preview
bot_id = 6145808069
```

The first run asks for that account's phone number and login code, so
it has to be run by hand once before it can be run unattended:

```shell
python preview.py
```

The account has to have started the bot at least once, or the bot has
no way to open the chat. `collect.config.PREVIEW_ACCOUNT` is the id the
bot expects to hear back from.

## Layout

Logic that does not know about Telegram lives at the top level —
`games/`, `stock/`, `gacha/`, `collect/`. The handlers that do live
under `func/`, and `handlers/register.py` wires the two together.

`share/` is a submodule shared with the other bots:

```shell
git submodule update --remote --merge share
```

State goes under `data/`, which is not tracked: balances, profit and
loss, and portfolios as pickles, the picture collection as SQLite plus a blob directory, and
`data/media/cache.db` remembering which pictures Telegram already holds
so the same gacha art is not re-uploaded every time.
