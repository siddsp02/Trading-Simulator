# !usr/bin/env python3

from dataclasses import InitVar, dataclass, field
from decimal import Decimal
from pprint import pprint

try:
    from market import Order, OrderStatus, Position, Trade, get_stock_price
    from technicals import Action
except ImportError:
    from src.market import Order, OrderStatus, Position, Trade, get_stock_price
    from src.technicals import Action


@dataclass
class Account:
    starting_balance: InitVar[int | Decimal]
    cash: Decimal = field(init=False)
    positions: dict[str, Position] = field(init=False, default_factory=dict)
    orders: list[Order] = field(init=False, default_factory=list)
    trades: list[Trade] = field(init=False, default_factory=list)

    def __post_init__(self, starting_balance: int | Decimal) -> None:
        self.balance = Decimal(starting_balance)

    def deposit(self, amount: Decimal) -> None:
        if amount < 0:
            raise ValueError("Can only deposit a non-negative amount of money.")
        self.balance += amount

    def withdraw(self, amount: Decimal) -> None:
        if amount > self.balance:
            raise ValueError("Cannot withdraw more money than you have.")
        if amount < 0:
            raise ValueError("Cannot withdraw a negative amount.")
        # You can withdraw a negative amount, which is just the same
        # as depositing. It's a weird way of doing the same thing,
        # but we'll allow it.
        self.balance -= amount

    @property
    def pnl(self) -> Decimal:
        return sum(pos.pnl for pos in self.positions.values())  # type: ignore

    @property
    def realized_pnl(self) -> Decimal:
        return sum(trade.realized_pnl for trade in self.trades)  # type:ignore

    @property
    def balance(self) -> Decimal:
        return self.cash

    @balance.setter
    def balance(self, amt: Decimal) -> None:
        if amt < 0:
            raise ValueError("Balance cannot be negative.")
        self.cash = amt

    @property
    def equity(self) -> Decimal:
        return self.balance + sum(pos.value for pos in self.positions.values())

    def close_positions(self, tickers: list[str] | None = None) -> None:
        tickers = list(self.positions) if tickers is None else tickers
        for ticker in tickers:
            self.sell_stock(ticker)

    def clear_filled_orders(self) -> None:
        self.orders[:] = (
            order for order in self.orders if order.status != OrderStatus.FILLED
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
    acc = Account(starting_balance=10_000)
    acc.buy_stock(ticker="AAPL", qty=10)
    acc.buy_stock(ticker="GOOGL", qty=5)
    acc.sell_stock(ticker="AAPL")
    pprint(acc)


if __name__ == "__main__":
    main()
