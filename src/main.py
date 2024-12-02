# !usr/bin/env python3

from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum
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
        self.qty += qty
        if qty > 0:
            self.price = (self.qty * self.price + qty * new_price) / self.qty

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

    @property
    def pnl(self) -> float:
        return sum(pos.pnl for pos in self.positions.values())

    @property
    def balance(self) -> float:
        return self.cash

    @balance.setter
    def balance(self, amt: float) -> None:
        self.cash = amt

    @property
    def equity(self) -> float:
        return self.balance + sum(pos.value for pos in self.positions.values())

    def execute_order(self, order: Order) -> None:
        match order.action:
            case Action.BUY:
                if order.size > self.balance:
                    raise ValueError("Insufficient funds to make trade.")
                self.balance -= order.size
                self.positions.setdefault(order.ticker, Position(order.ticker)).update(
                    order.qty, get_stock_price(order.ticker)
                )
            case Action.SELL:
                if order.ticker not in self.positions:
                    raise ValueError("Position in stock doesn't exist.")
                if order.qty > self.positions[order.ticker].qty:
                    raise ValueError("Can't sell more stocks than you own.")
                self.balance += order.size
                self.positions[order.ticker].update(-order.qty)
            case _:
                raise ValueError("Invalid action.")


def main() -> None:
    acc = Account(10_000.0)

    buy_order_1 = Order("AAPL", Action.BUY, qty=10)
    buy_order_2 = Order("GOOGL", Action.BUY, qty=10)

    sell_order_1 = Order("AAPL", Action.SELL, qty=10)
    sell_order_2 = Order("GOOGL", Action.SELL, qty=10)

    acc.execute_order(buy_order_1)
    acc.execute_order(buy_order_2)

    pprint(acc.positions)

    STOCK_PRICES["GOOGL"] = 300
    STOCK_PRICES["AAPL"] = 300

    acc.execute_order(sell_order_1)
    acc.execute_order(sell_order_2)

    pprint(acc.positions)
    print(acc.equity)


if __name__ == "__main__":
    main()
