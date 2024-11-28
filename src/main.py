# !usr/bin/env python3

from datetime import datetime
from enum import IntEnum
from functools import partial
from itertools import starmap
from pprint import pprint
from typing import NamedTuple

STOCK_PRICES = {"AAPL": 200, "GOOGL": 200, "MSFT": 400}


class Action(IntEnum):
    BUY = 0
    SELL = 1


class Status(IntEnum):
    UNFILLED = 0
    PARTIALLY_FILLED = 1
    FILLED = 2


class Order(NamedTuple):
    ticker: str
    action: Action
    qty: int
    status: Status = Status.UNFILLED
    timestamp: float = datetime.now().timestamp()


def get_stock_price(ticker: str) -> float:
    try:
        return STOCK_PRICES[ticker]
    except KeyError:
        raise LookupError(f'Stock with ticker "{ticker}" does not exist.')


class Position(NamedTuple):
    ticker: str
    qty: int
    price: float


def update_position(
    position: Position, add_qty: int, new_price: float | None = None
) -> Position:
    ticker, old_qty, old_price = position
    if new_price is None:
        new_price = get_stock_price(ticker)
    price = (old_qty * old_price + add_qty * new_price) / (old_qty + add_qty)
    qty = old_qty + add_qty
    return Position(ticker, qty, price)


def calc_pnl(ticker: str, avg_price: float, qty: int, pos: int) -> float:
    if qty > pos:
        raise ValueError("Can't sell more stocks than you own.")
    price = get_stock_price(ticker)
    return qty * (price - avg_price)


def calc_pnl_unrealized(ticker: str, position: Position) -> float:
    price = get_stock_price(ticker)
    return position.qty * (price - position.price)


def calc_total_pnl_unrealized(positions: dict[str, Position]) -> float:
    return sum(starmap(calc_pnl_unrealized, positions.items()))


def trade_stock(
    action: Action,
    ticker: str,
    positions: dict[str, Position],
    balance: float,
    qty: int,
) -> tuple[float, Order]:
    price = get_stock_price(ticker)
    order_size = qty * price

    match action:
        case Action.BUY:
            if order_size > balance:
                raise ValueError("Insufficient funds to make trade.")
            position = positions.get(ticker, Position(ticker, 0, price))
            positions[ticker] = update_position(position, qty, price)
            balance -= order_size
        case Action.SELL:
            ticker, old_qty, avg_price = positions[ticker]
            if qty > old_qty:
                raise ValueError("Can't sell more stocks than you own.")
            positions[ticker] = Position(ticker, old_qty - qty, avg_price)
            balance += order_size
        case _:
            raise ValueError("Invalid trading action.")

    return balance, Order(ticker, action, qty, Status.FILLED)


def calc_equity(balance: float, positions: dict[str, Position]) -> float:
    return (
        balance
        + sum(qty * price for _, qty, price in positions.values())
        + calc_total_pnl_unrealized(positions)
    )


buy_stock = partial(trade_stock, Action.BUY)
sell_stock = partial(trade_stock, Action.SELL)


def main() -> None:
    balance = 10_000.0
    positions = {}

    balance, order = buy_stock("AAPL", positions, balance, qty=10)

    print(order, balance, sep="\n")
    pprint(positions)
    print()

    balance, order = buy_stock("GOOGL", positions, balance, qty=10)

    print(order, balance, sep="\n")
    pprint(positions)
    print()

    STOCK_PRICES["GOOGL"] = 200
    STOCK_PRICES["AAPL"] = 500  # Update price.

    print(order, balance, sep="\n")
    pprint(positions)
    print()

    print(calc_equity(balance, positions))


if __name__ == "__main__":
    main()
