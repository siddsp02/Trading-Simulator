# !usr/bin/env python3

from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum
from pprint import pprint

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
    amount: int = 0
    filled: int = field(init=False, default=0)
    timestamp: float = datetime.now().timestamp()

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError("Can't make an order for a negative amount.")

    def fill(self, amount: int | None = None) -> None:
        if amount is None:
            self.filled = self.amount
        else:
            if amount < 0:
                raise ValueError("Amount to fill cannot be negative.")
            if amount > self.remaining:
                raise ValueError("Cannot fill more stocks than remaining in order.")
            self.filled += amount

    @property
    def remaining(self) -> int:
        return self.amount - self.filled

    @property
    def size(self) -> float:
        return self.amount * get_stock_price(self.ticker)

    @property
    def status(self) -> Status:
        if self.filled == self.amount:
            return Status.FILLED
        if 0 < self.filled < self.amount:
            return Status.PARTIALLY_FILLED
        return Status.UNFILLED


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

    def clear_filled_orders(self) -> None:
        self.orders[:] = (
            order for order in self.orders if order.status != Status.FILLED
        )

    def execute_pending_orders(self) -> None:
        for order in self.orders:
            self.execute_order(order)

    def make_order(self, ticker: str, action: Action, qty: int) -> Order:
        order = Order(ticker, action, qty)
        if order.size > self.balance:
            raise ValueError("Insufficient funds to make order.")
        self.orders.append(order)
        return order

    def execute_order(self, order: Order) -> None:
        ticker = order.ticker
        match order.action:
            case Action.BUY:
                self.balance -= order.size
                position = self.positions.setdefault(ticker, Position(ticker))
                position.update(order.amount)
                order.fill()
            case Action.SELL:
                position = self.positions[order.ticker]
                if order.amount > position.qty:
                    raise ValueError("Can't sell more stocks than you own.")
                self.balance += order.size
                position.update(-order.amount)
                order.fill()
            case _:
                raise ValueError("Invalid action.")


def main() -> None:
    acc = Account(10_000.0)
    order = acc.make_order("AAPL", Action.BUY, 10)
    print(order)
    pprint(acc)
    acc.execute_pending_orders()
    pprint(acc)
    acc.clear_filled_orders()
    pprint(acc)


if __name__ == "__main__":
    main()
