from typing import TYPE_CHECKING, List, Optional, TypeVar

import pandas as pd

from stock_market_analysis.src.backtest.backtest_entities import Holding, TransactionLog
from stock_market_analysis.src.output.csv_output import CSVOutput
from stock_market_analysis.src.output.plot_output import PlotOutput
from stock_market_analysis.src.utils.utils import check_columns_exist_in_df


if TYPE_CHECKING:
    from stock_market_analysis.src.output.base_output import BaseOutput

Self = TypeVar("Self", bound="BacktestService")


class BacktestService:
    """Performs stock strategy backtesting."""

    def __init__(
        self: Self,
        df: pd.DataFrame,
        backtest_amounts: List[int],
        max_stock_amount: float,
    ) -> None:
        """Config BacktestService intially."""
        self.df = df
        self.backtest_amounts = backtest_amounts
        self.max_stock_amount = max_stock_amount
        self.holdings: List[Holding] = []
        self.backtest_df = pd.DataFrame()
        self.TRANSACTION_FEE = 11.95
        self.columns_to_plot: list[str] = []

    def perform_buy(self: Self, row: pd.Series, amount: float) -> None:
        """Perform a buy transaction."""
        price = row["Close"]
        shares = int(amount // price)
        total_investment = shares * price + self.TRANSACTION_FEE

        holding = Holding(
            ticker=row["Ticker"],
            buy_price=price,
            shares=shares,
            total_investment=total_investment,
        )
        self.holdings.append(holding)

        transaction_log = TransactionLog(  # type: ignore
            date=row["Date"],
            ticker=row["Ticker"],
            transaction="buy",
            hold_shares_number=shares,
            transaction_amount=-total_investment,
        )
        self.backtest_df = pd.concat(
            [self.backtest_df, pd.DataFrame([transaction_log.dict()])]
        )

    def perform_sell(self: Self, row: pd.Series, holding: Holding) -> None:
        """Perform a sell transaction."""
        price = row["Close"]
        total_sale = holding.shares * price - self.TRANSACTION_FEE
        yield_amount = total_sale - holding.total_investment
        yield_percent = (yield_amount / holding.total_investment) * 100

        self.holdings.remove(holding)

        transaction_log = TransactionLog(
            date=row["Date"],
            ticker=row["Ticker"],
            transaction="sell",
            hold_shares_number=holding.shares,
            transaction_amount=total_sale,
            yield_amount=yield_amount,
            yield_percent=yield_percent,
        )
        self.backtest_df = pd.concat(
            [self.backtest_df, pd.DataFrame([transaction_log.dict()])]
        )

    def run(self: Self) -> None:
        """Run main method to run the backtest."""
        check_columns_exist_in_df(self.df, ["Ticker", "main_advice", "Close"])

        for _, row in self.df.iterrows():
            if row["main_advice"] == "buy" and len(self.holdings) < len(
                self.backtest_amounts
            ):
                self.perform_buy(row, self.backtest_amounts[len(self.holdings)])
            elif row["main_advice"] == "sell":
                for holding in self.holdings:
                    if holding.ticker == row["Ticker"]:
                        self.perform_sell(row, holding)

    def get_portfolio(self: Self) -> pd.DataFrame:
        """Calculate portfolio value and add a summary row at the bottom."""
        portfolio = [
            {
                "Ticker": h.ticker,
                "Shares": h.shares,
                "Buy Price": h.buy_price,
                "Total Investment": h.total_investment,
            }
            for h in self.holdings
        ]

        portfolio_df = pd.DataFrame(portfolio)

        if not portfolio_df.empty:
            summary = {
                "Ticker": "TOTAL",
                "Shares": portfolio_df["Shares"].sum(),
                "Buy Price": "-",  # No meaningful average for this
                "Total Investment": portfolio_df["Total Investment"].sum(),
            }
            portfolio_df = pd.concat(
                [portfolio_df, pd.DataFrame([summary])], ignore_index=True
            )

        return portfolio_df

    def get_backtest_log(self: Self) -> pd.DataFrame:
        """Return backtest transaction log."""
        return self.backtest_df

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
            output.render(data_df, output_file, self.columns_to_plot)
        else:
            msg = "Unsupported output format."
            raise ValueError(msg)
