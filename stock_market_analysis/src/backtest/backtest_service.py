from typing import TYPE_CHECKING, List, Optional, TypeVar

import pandas as pd
from rich.progress import Progress

from stock_market_analysis.src.backtest.backtest_entities import Holding, TransactionLog
from stock_market_analysis.src.output.csv_output import CSVOutput
from stock_market_analysis.src.output.plot_output import PlotOutput


if TYPE_CHECKING:
    from stock_market_analysis.src.output.base_output import BaseOutput

Self = TypeVar("Self", bound="BacktestService")


class BacktestService:
    """Performs stock strategy backtesting."""

    TRANSACTION_FEE = 11.95

    def output_data(
        self: Self,
        data_df: pd.DataFrame,
        output_format: str,
        output_file: Optional[str] = None,
    ) -> None:
        """Save data to one of the formats."""
        # Output data
        output: BaseOutput | None = None
        if output_format == "csv":
            output = CSVOutput()
            output.render(data_df, output_file)
        elif output_format == "plot":
            output = PlotOutput()
            output.render(data_df, output_file, self.columns_to_plot) # type: ignore
        else:
            msg = "Unsupported output format."
            raise ValueError(msg)

    def __init__(
        self: Self,
        df: pd.DataFrame,
        backtest_amounts: List[int],
        max_stock_amount: float,
        min_stock_amount: float,
    ) -> None:
        """Config of BacktestService."""
        self.df = df
        self.initial_cash = sum(backtest_amounts)
        self.remaining_cash = self.initial_cash
        self.backtest_amounts = backtest_amounts
        self.max_stock_amount = max_stock_amount
        self.min_stock_amount = min_stock_amount
        self.holdings: List[Holding] = []
        self.backtest_df = pd.DataFrame()
        self.total_value = self.initial_cash  # Start with total cash as initial value

    def perform_buy(self: Self, row: pd.Series, amount: float) -> None:
        """Perform a buy transaction if there's enough cash available."""
        price = row["Close"] / 100
        max_available_amount = min(amount, self.remaining_cash) - self.TRANSACTION_FEE
        shares = int(max_available_amount // price)
        total_investment = shares * price + self.TRANSACTION_FEE

        if shares > 0 and self.remaining_cash >= total_investment:
            # Buy the stock and update remaining cash
            holding = Holding(
                ticker=row["Ticker"],
                buy_price=price,
                shares=shares,
                total_investment=total_investment,
            )
            self.holdings.append(holding)
            self.remaining_cash -= total_investment

            # Log the transaction
            self.log_transaction(
                row["Date"], row["Ticker"], "buy", shares, -total_investment, price
            )

    def perform_sell(self: Self, row: pd.Series, holding: Holding) -> None:
        """Perform a sell transaction and update remaining cash."""
        price = row["Close"] / 100
        total_sale = holding.shares * price - self.TRANSACTION_FEE
        yield_amount = total_sale - holding.total_investment
        yield_percent = (yield_amount / holding.total_investment) * 100

        self.holdings.remove(holding)

        # Add the sale value to the remaining cash
        self.remaining_cash += total_sale

        # Log the transaction
        self.log_transaction(
            row["Date"],
            holding.ticker,
            "sell",
            holding.shares,
            total_sale,
            price,
            yield_amount,
            yield_percent,
        )

    def log_transaction(  # noqa: PLR0913
        self: Self,
        date: pd.Timestamp,
        ticker: str,
        transaction: str,
        shares: int,
        transaction_amount: float,
        close_price: float,
        yield_amount: float = 0.0,  # noqa: ARG002
        yield_percent: float = 0.0,  # noqa: ARG002
    ) -> None:
        """Log each transaction with updated cash and portfolio value."""
        total_value = self.calculate_total_value()
        total_yield = total_value - self.initial_cash
        total_yield_percent = (total_yield / self.initial_cash) * 100

        # Create the log entry
        log_entry = TransactionLog(
            date=date,
            ticker=ticker,
            transaction=transaction,
            close_price=close_price,
            hold_shares_number=shares,
            transaction_amount=transaction_amount,
            available_cash=self.remaining_cash,
            total_value=total_value,
            total_yield=total_yield,
            total_yield_percent=total_yield_percent,
        ).dict()

        # Append the log entry to the DataFrame
        self.backtest_df = pd.concat([self.backtest_df, pd.DataFrame([log_entry])])

    def calculate_total_value(self: Self) -> float:
        """Calculate total value of holdings and available cash."""
        holdings_value = sum(h.shares * h.buy_price for h in self.holdings)
        return holdings_value + self.remaining_cash

    def initial_purchases(self: Self) -> None:
        """Perform initial purchases based on backtest_amounts."""
        idx = 0
        for _, row in self.df.iterrows():
            if row["main_advice"] == "buy" and idx < len(self.backtest_amounts):
                # Use the specified amount for the initial purchase
                self.perform_buy(row, self.backtest_amounts[idx])
                idx += 1

            # Stop when all initial backtest_amounts are used
            if idx >= len(self.backtest_amounts):
                break

    def run(self: Self) -> None:
        """Run the backtest by iterating through the DataFrame rows with progress tracking."""
        # Perform initial purchases
        self.initial_purchases()

        with Progress() as progress:
            task = progress.add_task("[green]Running backtest...", total=len(self.df))

            for _idx, row in self.df.iterrows():
                # Check for sell signals first
                if row["main_advice"] == "sell":
                    for holding in self.holdings:
                        if holding.ticker == row["Ticker"]:
                            self.perform_sell(row, holding)

                # Then check for buy signals if enough cash is available
                elif (
                    row["main_advice"] == "buy"
                    and self.remaining_cash >= self.min_stock_amount
                ):
                    self.perform_buy(row, self.max_stock_amount)

                # Update progress bar
                progress.update(task, advance=1)

    def get_portfolio(self: Self) -> pd.DataFrame:
        """Return a summary of the current portfolio with holdings, cash.

        and portfolio value based on today's 'Close' price from Yahoo Finance.
        """
        tickers = [holding.ticker for holding in self.holdings]

        # Retrieve the latest close prices for all tickers in holdings
        # TODO(damian): get data from original data provider and get data based on provided period
        import yfinance as yf

        current_prices = yf.download(tickers, period="1d")["Close"].to_dict()
        current_prices = {
            ticker: next(iter(values.values())) / 100
            for ticker, values in current_prices.items()
        }

        portfolio = []
        for holding in self.holdings:
            # Get the latest close price for each ticker
            current_close_price = current_prices.get(holding.ticker, holding.buy_price)
            current_value = holding.shares * current_close_price
            portfolio.append(
                {
                    "Ticker": holding.ticker,
                    "Shares": holding.shares,
                    "Current Close Price": current_close_price,  # Use today's close price
                    "Total Investment": current_value,
                }
            )

        portfolio_df = pd.DataFrame(portfolio)

        # Add available cash to the portfolio
        available_cash_row = pd.DataFrame(
            [
                {
                    "Ticker": "CASH",
                    "Shares": "-",
                    "Current Close Price": "-",
                    "Total Investment": self.remaining_cash,
                }
            ]
        )

        if not portfolio_df.empty:
            # Summarize the total portfolio value
            summary = {
                "Ticker": "TOTAL",
                "Shares": portfolio_df["Shares"].sum(),
                "Current Close Price": "-",
                "Total Investment": portfolio_df["Total Investment"].sum()
                + self.remaining_cash,
            }
            portfolio_df = pd.concat(
                [portfolio_df, available_cash_row, pd.DataFrame([summary])],
                ignore_index=True,
            )

        return portfolio_df

    def get_backtest_log(self: Self) -> pd.DataFrame:
        """Return the transaction log."""
        return self.backtest_df
