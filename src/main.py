# !usr/bin/env python3

from dataclasses import InitVar, dataclass, field
from datetime import datetime
from enum import IntEnum

from technicals import Action

STOCK_PRICES = {"AAPL": 200, "GOOGL": 200, "MSFT": 400}


class Status(IntEnum):
    UNFILLED = 0
    PARTIALLY_FILLED = 1
    FILLED = 2


@dataclass
class Order:
    ticker: str
    action: Action
    amount: int = 0
    price: float = field(init=False)
    filled: int = field(init=False, default=0)
    timestamp: float = datetime.now().timestamp()

    def __str__(self) -> str:
        return f"<{self.action.name} {self.ticker} @ {self.price} ({self.filled}/{self.amount} filled)>"

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError("Can't make an order for a negative amount.")
        if self.action not in Action:
            raise ValueError("Invalid Action.")
        self.price = get_stock_price(self.ticker)

    def fill(self, amount: int | None = None) -> None:
        if amount is None:
            self.filled = self.amount
        else:
            if amount < 0:
                raise ValueError("Amount to fill cannot be negative.")
            if amount > self.remaining:
                raise ValueError("Cannot fill more stocks than remaining in order.")
            self.filled += amount

    def get_size(self, absval: bool = True) -> float:
        return self.size if (self.action == Action.BUY or absval) else -self.size

    @property
    def remaining(self) -> int:
        return self.amount - self.filled

    @property
    def size(self) -> float:
        return self.amount * self.price

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

    def update_from_order(self, order: Order) -> None:
        self.update(order.amount if order.action == Action.BUY else -order.amount)
        order.fill()

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
class Trade:
    position: InitVar[Position]
    order: Order
    entry_price: float = field(init=False)
    timestamp: float = datetime.now().timestamp()

    def __post_init__(self, position: Position) -> None:
        if position.qty > self.order.amount:
            raise ValueError()
        self.entry_price = position.price

    @property
    def realized_pnl(self) -> float:
        return (self.order.price - self.entry_price) * self.order.amount


@dataclass
class Account:
    starting_balance: InitVar[float]
    cash: float = field(init=False)
    positions: dict[str, Position] = field(init=False, default_factory=dict)
    orders: list[Order] = field(init=False, default_factory=list)
    trades: list[Trade] = field(init=False, default_factory=list)

    def __post_init__(self, starting_balance: float) -> None:
        if starting_balance < 0:
            raise ValueError("Funds cannot be negative.")
        self.balance = starting_balance

    def deposit(self, amount: float) -> None:
        if amount < 0:
            raise ValueError("Can only deposit a non-negative amount of money.")
        self.balance += amount

    def withdraw(self, amount: float) -> None:
        if amount > self.balance:
            raise ValueError("Cannot withdraw more money than you have.")
        if amount < 0:
            raise ValueError("Cannot withdraw a negative amount.")
        # You can withdraw a negative amount, which is just the same
        # as depositing. It's a weird way of doing the same thing,
        # but we'll allow it.
        self.balance -= amount

    @property
    def pnl(self) -> float:
        return sum(pos.pnl for pos in self.positions.values())

    @property
    def realized_pnl(self) -> float:
        return sum(trade.realized_pnl for trade in self.trades)

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

    def close_positions(self, tickers: list[str] | None = None) -> None:
        tickers = list(self.positions) if tickers is None else tickers
        for ticker in tickers:
            self.sell_stock(ticker)

    def clear_filled_orders(self) -> None:
        self.orders[:] = (
            order for order in self.orders if order.status != Status.FILLED
        )

    def execute_pending_orders(self) -> None:
        for order in self.orders:
            self.execute_order(order)

    def make_order(self, ticker: str, action: Action, qty: int) -> Order:
        order = Order(ticker, action, qty)
        match action:
            case Action.BUY:
                if order.size > self.balance:
                    raise ValueError("Insufficient funds to make order.")
            case Action.SELL:
                if qty > self.positions[ticker].qty:
                    raise ValueError("Can't sell more stocks than you own")
        self.orders.append(order)
        return order

    def execute_order(self, order: Order) -> None:
        ticker = order.ticker
        position = self.positions.setdefault(ticker, Position(ticker))
        position.update_from_order(order)
        self.balance -= order.get_size(absval=False)

    def buy_stock(self, ticker: str, qty: int | None = None) -> None:
        if qty is None:
            qty = int(self.balance / get_stock_price(ticker))
        order = self.make_order(ticker, Action.BUY, qty)
        self.execute_order(order)

    def sell_stock(self, ticker: str, qty: int | None = None) -> None:
        if qty is None:
            qty = self.positions[ticker].qty
        order = self.make_order(ticker, Action.SELL, qty)
        self.execute_order(order)
        self.trades.append(Trade(self.positions[ticker], order))

    def make_and_execute_order(self, ticker: str, action: Action, qty: int) -> None:
        match action:
            case Action.BUY:
                self.buy_stock(ticker, qty)
            case Action.SELL:
                self.sell_stock(ticker, qty)
            case _:
                raise ValueError("Invalid action.")


def main() -> None:
    acc = Account(starting_balance=10_000.0)
    acc.buy_stock(ticker="AAPL", qty=10)
    acc.buy_stock(ticker="GOOGL", qty=5)
    acc.sell_stock(ticker="AAPL")


if __name__ == "__main__":
    main()
