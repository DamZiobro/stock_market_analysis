import copy
from typing import TYPE_CHECKING, List, Optional, TypeVar

import pandas as pd
from rich.progress import Progress

from stock_market_analysis.src.backtest.backtest_entities import Holding, TransactionLog
from stock_market_analysis.src.data_providers.yahoo_data import yf_download
from stock_market_analysis.src.output.csv_output import CSVOutput
from stock_market_analysis.src.output.plot_output import PlotOutput
from stock_market_analysis.src.utils.utils import inject_missing_dates


if TYPE_CHECKING:
    from stock_market_analysis.src.output.base_output import BaseOutput

Self = TypeVar("Self", bound="BacktestService")


class BacktestService:
    """Performs stock strategy backtesting."""

    TRANSACTION_FEE = 11.95
    DROP_7_PERCENT = 0.93  # for 7% rule stop/loss

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
            output.render(data_df, output_file, self.columns_to_plot)  # type: ignore
        else:
            msg = "Unsupported output format."
            raise ValueError(msg)

    def __init__(  # noqa: PLR0913
        self: Self,
        df: pd.DataFrame,
        backtest_amounts: List[int],
        max_stock_amount: float,
        min_stock_amount: float,
        backtesting_period: str,
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
        self.backtesting_period = backtesting_period

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
                stock_index=row["Stock_Index"],
                buy_date=row["Date"],
                buy_price=price,
                shares=shares,
                total_investment=total_investment,
                sell_price_stop_loss=price
                * self.DROP_7_PERCENT,  # for 7% rule stop/loss
                full_data=yf_download(row["Ticker"], self.backtesting_period),
            )
            self.holdings.append(holding)
            self.remaining_cash -= total_investment

            # Log the transaction
            self.log_transaction(
                row["Date"],
                row["Ticker"],
                row["Stock_Index"],
                "buy",
                shares,
                -total_investment,
                price,
            )

    def perform_sell(
        self: Self, row: pd.Series, holding: Holding, suffix: str = ""
    ) -> None:
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
            holding.stock_index,
            f"sell{suffix}",
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
        stock_index: str,
        transaction: str,
        shares: int,
        transaction_amount: float,
        close_price: float,
        yield_amount: float = 0.0,
        yield_percent: float = 0.0,
    ) -> None:
        """Log each transaction with updated cash and portfolio value."""
        total_value = self.calculate_total_value()
        total_yield = total_value - self.initial_cash
        total_yield_percent = (total_yield / self.initial_cash) * 100

        # Create the log entry
        log_entry = TransactionLog(
            date=date,
            ticker=ticker,
            stock_index=stock_index,
            transaction=transaction,
            close_price=close_price,
            hold_shares_number=shares,
            transaction_amount=transaction_amount,
            yield_amount=yield_amount,
            yield_percent=yield_percent,
            available_cash=self.remaining_cash,
            total_value=total_value,
            total_yield=total_yield,
            total_yield_percent=total_yield_percent,
        ).dict()

        # Append the log entry to the DataFrame
        log_entry_df = pd.DataFrame([log_entry])
        self.backtest_df = pd.concat([self.backtest_df, log_entry_df])

    def calculate_total_value(self: Self) -> float:
        """Calculate total value of holdings and available cash."""
        holdings_value = sum(h.shares * h.buy_price for h in self.holdings)
        return holdings_value + self.remaining_cash

    def run(self: Self) -> None:
        """Run the backtest by iterating through the DataFrame rows with progress tracking."""
        # Perform initial purchases

        self.df = inject_missing_dates(self.df, self.backtesting_period)

        with Progress() as progress:
            task = progress.add_task("[green]Backtesting...", total=len(self.df))

            for _, row in self.df.iterrows():

                # Check for sell signals first
                for holding in self.holdings:
                    row_close_price = (
                        holding.full_data.loc[row["Date"]]["Close"]
                        if row["Date"] in holding.full_data.index
                        and row["Date"] > holding.buy_date
                        else None
                    )
                    if holding.ticker == row["Ticker"] and row["main_advice"] == "sell":
                        # sell because of detected 'sell' signal
                        self.perform_sell(row, holding, "_signal")
                    elif (
                        row_close_price
                        and row_close_price <= holding.sell_price_stop_loss * 100
                    ):
                        # sell because of stop / loss
                        if row_close_price:
                            row_copy = copy.deepcopy(row)
                            row_copy["Close"] = row_close_price
                            row_copy["main_advice"] = "sell"  # to avoid buy below
                        self.perform_sell(row_copy, holding, "_stop_loss")

                # initial_purchases - if backtest_amounts contains money, then get from there
                idx = 0
                if (
                    row["main_advice"] == "buy"
                    and idx < len(self.backtest_amounts)
                    and self.remaining_cash >= self.min_stock_amount
                ):
                    # Use the specified amount for the initial purchase
                    self.perform_buy(row, self.backtest_amounts[idx])
                    idx += 1
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

        def get_latest_price(series: pd.Series) -> float | None:
            # Remove NaN values and get the last available price
            non_nan_series = series.dropna()
            if len(non_nan_series) > 0:
                return non_nan_series.iloc[-1] / 100
            return None  # or you could return a default value or raise an exception

        if not self.holdings:
            return pd.DataFrame([])

        recent_prices = {
            holding.ticker: get_latest_price(holding.full_data["Close"])
            for holding in self.holdings
        }

        portfolio = []
        for holding in self.holdings:
            # Get the latest close price for each ticker
            current_close_price = recent_prices.get(holding.ticker)
            current_value = holding.shares * current_close_price
            portfolio.append(
                {
                    "Ticker": holding.ticker,
                    "Stock_Index": holding.stock_index,
                    "Shares": holding.shares,
                    "Recent Close Price": current_close_price,  # Use today's close price
                    "Total Investment": current_value,
                }
            )

        portfolio_df = pd.DataFrame(portfolio)

        # Add available cash to the portfolio
        available_cash_row = pd.DataFrame(
            [
                {
                    "Ticker": "CASH",
                    "Stock_Index": "CASH",
                    "Shares": "-",
                    "Recent Close Price": "-",
                    "Total Investment": self.remaining_cash,
                }
            ]
        )

        if not portfolio_df.empty:
            # Summarize the total portfolio value
            summary = {
                "Ticker": "TOTAL",
                "Stock_Index": "-",
                "Shares": "-",
                "Recent Close Price": "-",
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
