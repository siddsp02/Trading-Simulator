# !usr/bin/env python3

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum
from pprint import pprint
from typing import Any, Iterable, NamedTuple

STOCK_PRICES = {"AAPL": 200, "GOOGL": 200, "MSFT": 400}


class Action(IntEnum):
    BUY = 0
    SELL = 1


class Status(IntEnum):
    UNFILLED = 0
    PARTIALLY_FILLED = 1
    FILLED = 2


@dataclass
class Order:
    ticker: str
    action: Action
    qty: int
    status: Status = Status.UNFILLED
    timestamp: float = datetime.now().timestamp()

    @property
    def size(self) -> float:
        return self.qty * get_stock_price(self.ticker)


def get_stock_price(ticker: str) -> float:
    try:
        return STOCK_PRICES[ticker]
    except KeyError:
        raise LookupError(f'Stock with ticker "{ticker}" does not exist.')


@dataclass
class Position:
    ticker: str
    qty: int = 0
    price: float = 0

    def update(self, qty: int, new_price: float | None = None) -> None:
        if new_price is None:
            new_price = get_stock_price(self.ticker)
        if qty > 0:
            self.price = (self.qty * self.price + qty * new_price) / (self.qty + qty)
        self.qty += qty

    @property
    def pnl(self) -> float:
        price = get_stock_price(self.ticker)
        return self.qty * (price - self.price)

    @property
    def value(self) -> float:
        price = get_stock_price(self.ticker)
        return self.qty * price


@dataclass
class Account:
    cash: float
    positions: dict[str, Position] = field(init=False, default_factory=dict)
    orders: list[Order] = field(init=False, default_factory=list)

    def __post_init__(self) -> None:
        if self.cash < 0:
            raise ValueError("Funds cannot be negative.")

    @property
    def pnl(self) -> float:
        return sum(pos.pnl for pos in self.positions.values())

    @property
    def balance(self) -> float:
        return self.cash

    @balance.setter
    def balance(self, amt: float) -> None:
        if amt < 0:
            raise ValueError("Balance cannot be negative.")
        self.cash = amt

    @property
    def equity(self) -> float:
        return self.balance + sum(pos.value for pos in self.positions.values())

    def execute_pending_orders(self) -> None:
        for order in self.orders:
            self.execute_order(order)

    def make_order(self, ticker: str, action: Action, qty: int) -> None:
        self.orders.append(Order(ticker, action, qty))

    def execute_order(self, order: Order) -> None:
        match order.action:
            case Action.BUY:
                if order.size > self.balance:
                    raise ValueError("Insufficient funds to make trade.")
                self.balance -= order.size
                self.positions.setdefault(order.ticker, Position(order.ticker)).update(
                    order.qty
                )
                order.status = Status.FILLED
            case Action.SELL:
                if order.ticker not in self.positions:
                    raise ValueError("Position in stock doesn't exist.")
                if order.qty > self.positions[order.ticker].qty:
                    raise ValueError("Can't sell more stocks than you own.")
                self.balance += order.size
                self.positions[order.ticker].update(-order.qty)
                order.status = Status.FILLED
            case _:
                raise ValueError("Invalid action.")


def main() -> None:
    acc = Account(10_000.0)

    acc.make_order(ticker="AAPL", action=Action.BUY, qty=10)
    acc.make_order(ticker="GOOGL", action=Action.BUY, qty=10)

    pprint(acc)
    acc.execute_pending_orders()
    pprint(acc)


if __name__ == "__main__":
    main()
