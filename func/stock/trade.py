from typing import Optional
from share.auth import ensure_auth
from telethon.tl.custom import Message
from share.common import get_command_args
from games.balance import money, user_balance
from stock.main import price_of
from stock.req import get_quotes
from stock.tools import is_trading_time
from stock.quote import CN, Quote, is_index, market_of, normalize
from stock.portfolio import LOT_SIZE, Trade, portfolio


ALL_WORDS = {'all', '全部', '清仓', '梭哈', '全仓'}

BUY_USAGE = '用法：`/buy 600519 100`，或 `/buy 600519 all` 有多少买多少。'
SELL_USAGE = '用法：`/sell 600519 100`，或 `/sell 600519 all` 清仓。'


def tradeable(code: str) -> Optional[str]:
    """
    Why this symbol cannot be dealt, or None if it can.

    A shares only: the balance is in yuan, and pretending to buy Apple
    with it would mean inventing an exchange rate.
    """
    if market_of(code) != CN:
        return '只能买卖 A 股，港股美股暂时只能看。'
    if is_index(code):
        return '指数不能买卖，试试成分股。'
    return None


def parse_shares(word: str) -> Optional[int]:
    try:
        shares = int(float(word))
    except (TypeError, ValueError):
        return None
    if shares <= 0 or shares % LOT_SIZE:
        return None
    return shares


def closed_note() -> str:
    return '' if is_trading_time() else '\n（已休市，按最新价成交）'


def receipt(action: str, quote: Quote, trade: Trade, balance: float) -> str:
    lines = [
        f'**{action} {quote.name}（{quote.symbol}）**',
        f'{trade.shares} 股 × {trade.price:.2f} = {money(trade.gross)}',
        f'手续费 {money(trade.fees)}',
    ]
    if trade.profit is not None:
        lines.append(f'到账 {money(trade.cash)}，盈亏 **{trade.profit:+,.2f}**')
    else:
        lines.append(f'共付 {money(trade.cash)}')

    lines.append(f'余额 {money(balance)}')
    return '\n'.join(lines) + closed_note()


@ensure_auth
async def command_buy(event) -> Message:
    args = get_command_args(event.raw_text)
    if not args:
        return await event.respond(BUY_USAGE)

    code = normalize(args[0])
    if not code:
        return await event.respond(BUY_USAGE)
    complaint = tradeable(code)
    if complaint:
        return await event.respond(complaint)

    quote = await price_of(code)
    if not quote or not quote.tradeable:
        return await event.respond(f'`{args[0]}` 现在没有报价，买不了。')

    user_id = event.sender_id
    balance = user_balance.get_balance(user_id)
    word = args[1] if len(args) > 1 else ''

    if word.lower() in ALL_WORDS:
        # drop a lot at a time until the fees fit too, rather than
        # failing at the last step over five yuan of commission
        lots = int(balance // (quote.price * LOT_SIZE))
        while lots and portfolio.quote_buy(code, lots * LOT_SIZE, quote.price).cash > balance:
            lots -= 1
        shares = lots * LOT_SIZE
        if shares <= 0:
            return await event.respond(
                f'余额 {money(balance)} 买不起一手 {quote.name}'
                f'（{money(quote.price * LOT_SIZE)}）。')
    else:
        shares = parse_shares(word)
        if not shares:
            return await event.respond(f'股数得是 {LOT_SIZE} 的整数倍。\n{BUY_USAGE}')

    trade = portfolio.quote_buy(code, shares, quote.price)
    if not user_balance.subtract_balance(user_id, trade.cash):
        return await event.respond(
            f'余额不足：需要 {money(trade.cash)}，你有 {money(balance)}。')

    portfolio.apply_buy(user_id, trade)
    held = portfolio.holding(user_id, code)
    text = receipt('买入', quote, trade, user_balance.get_balance(user_id))
    text += f'\n现持 {held.shares} 股，成本 {held.average:.3f}'
    return await event.respond(text)


@ensure_auth
async def command_sell(event) -> Message:
    args = get_command_args(event.raw_text)
    if not args:
        return await event.respond(SELL_USAGE)

    code = normalize(args[0])
    if not code:
        return await event.respond(SELL_USAGE)

    user_id = event.sender_id
    held = portfolio.holding(user_id, code)
    if not held.shares:
        return await event.respond(f'你没有 `{args[0]}` 的持仓。')

    quote = await price_of(code)
    if not quote or not quote.tradeable:
        return await event.respond(f'`{args[0]}` 现在没有报价，卖不了。')

    word = args[1] if len(args) > 1 else ''
    if not word or word.lower() in ALL_WORDS:
        shares = held.shares
    else:
        shares = parse_shares(word)
        if not shares:
            return await event.respond(f'股数得是 {LOT_SIZE} 的整数倍。\n{SELL_USAGE}')
        if shares > held.shares:
            return await event.respond(f'你只有 {held.shares} 股。')

    trade = portfolio.quote_sell(user_id, code, shares, quote.price)
    portfolio.apply_sell(user_id, trade)
    balance = user_balance.add_balance(user_id, trade.cash)

    text = receipt('卖出', quote, trade, balance)
    left = portfolio.holding(user_id, code)
    text += f'\n剩余 {left.shares} 股' if left.shares else '\n已清仓'
    return await event.respond(text)


@ensure_auth
async def command_position(event) -> Message:
    user_id = event.sender_id
    book = portfolio.holdings(user_id)
    cash = user_balance.get_balance(user_id)

    if not book:
        return await event.respond(
            f'你还没有持仓。\n现金 {money(cash)}\n\n{BUY_USAGE}')

    quotes = await get_quotes(list(book))
    lines = ['**持仓**', '']
    market_value = 0.0
    total_cost = 0.0

    for code, held in book.items():
        quote = quotes.get(code)
        price = quote.price if quote and quote.tradeable else held.average
        name = quote.name if quote else code
        value = price * held.shares
        profit = value - held.cost
        ratio = profit / held.cost if held.cost else 0
        market_value += value
        total_cost += held.cost

        lines.append(f'**{name}**（{code[2:]}）')
        lines.append(f'　{held.shares} 股　成本 {held.average:.3f}　现价 {price:.3f}')
        lines.append(f'　市值 {money(value)}　浮盈 **{profit:+,.2f}**（{ratio:+.2%}）')

    total_profit = market_value - total_cost
    lines += [
        '',
        f'市值 {money(market_value)}　浮盈 **{total_profit:+,.2f}**',
        f'现金 {money(cash)}',
        f'总资产 **{money(market_value + cash)}**',
    ]
    return await event.respond('\n'.join(lines) + closed_note())
