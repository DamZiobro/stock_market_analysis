from typing import ClassVar, Optional, TypeVar

import pandas as pd

from stock_market_analysis.src.analysis.filtering import FilterBy
from stock_market_analysis.src.analysis.sorting import SortBy
from stock_market_analysis.src.data_providers.yahoo_data import YahooDataProvider
from stock_market_analysis.src.services.base_service import BaseAnalysisService
from stock_market_analysis.src.strategies.macd import MACDDay3BuyDay3SellStrategy
from stock_market_analysis.src.strategies.rsi import RSIOverboughtOversoldStrategy
from stock_market_analysis.src.utils.utils import (
    execute_buy,
    execute_sell,
    find_buy_signals,
)


Self = TypeVar("Self", bound="MACD3DaysRSIService")


class MACD3DaysRSIService(BaseAnalysisService):
    """Facade service for stock market analysis."""

    data_provider: ClassVar = YahooDataProvider()  # type: ignore
    technical_indicators: ClassVar = ["rsi", "macd"]
    pre_run_strategies: ClassVar = [
        RSIOverboughtOversoldStrategy(),
        MACDDay3BuyDay3SellStrategy(),
    ]  # type: ignore
    post_run_analysis_list: ClassVar = [
        FilterBy(filters={"macd_advice": [("IN", "sell|buy")]}),
        SortBy(
            columns=["Date", "macd_advice", "rsi_category", "macd_hist", "Ticker"],
            orders_asc=[True, True, True, False, True],
        ),
    ]  # type: ignore
    columns_to_plot: ClassVar = [*technical_indicators, "Close"]  # type: ignore

    # def backtest(
    #     self: Self,
    #     data_df: pd.DataFrame,
    #     backtest_amounts: Optional[list[int]] = [
    #         3000,
    #         3000,
    #         4000,
    #     ],
    # ) -> pd.DataFrame:
    #     """Backtest analysis."""
    #     data_df = data_df.reset_index()
    #     oldest_date = data_df["Date"].iloc[0].date()
    #     new_buys_df = (
    #         FilterBy(filters={"Date": oldest_date, "macd_advice": "buy"})
    #         .apply(data_df)
    #         .tail(len(backtest_amounts))
    #     )

    #     for i, (_, row) in enumerate(new_buys_df.iterrows()):
    #         tran_date = row["Date"]
    #         tran_ticker = row["Ticker"]
    #         hold_shares = math.floor(backtest_amounts[i] / row["Close"])
    #         invested_amount = hold_shares * row["Close"]
    #         logger.info(
    #             "Buying %d shares of %s for %f",
    #             hold_shares,
    #             tran_ticker,
    #             invested_amount,
    #         )
    #         new_buys_df.loc[
    #             (new_buys_df["Ticker"] == tran_ticker)
    #             & (new_buys_df["Date"] == tran_date),
    #             "invested_amount",
    #         ] = invested_amount
    #         new_buys_df.loc[
    #             (new_buys_df["Ticker"] == tran_ticker)
    #             & (new_buys_df["Date"] == tran_date),
    #             "hold_shares",
    #         ] = hold_shares

    #     return new_buys_df

    def backtest(
        self: Self,
        df: pd.DataFrame,
        backtest_amounts: Optional[list[int]] = [  # noqa: B006
            3000,
            3000,
            4000,
        ],
    ) -> pd.DataFrame:
        """Backtest the trading strategy on the given DataFrame.

        Args:
        ----
        df (pd.DataFrame): Input DataFrame with 'ticker', 'Date', 'Close', and 'signal' columns.
        backtest_amounts (List[int]): Initial distribution of backtest amounts.

        Returns:
        -------
        pd.DataFrame: DataFrame with backtesting results.
        """
        if backtest_amounts is None:
            backtest_amounts = []

        df = df.reset_index()
        df["main_advice"] = df["macd_advice"]
        results = []
        holdings = {}

        #TODO(damian): include remaining subamounts from holdings into future transactions
        buy_signals = find_buy_signals(df, len(backtest_amounts))
        for (ticker, date), amount in zip(buy_signals, backtest_amounts):
            transaction = execute_buy(df, ticker, date, amount)
            holdings[ticker] = transaction
            #TODO(damian): copy rows from original table instead of crete new ones
            results.append(
                {
                    "Date": date,
                    "ticker": ticker,
                    "action": "buy",
                    "hold_shares": transaction["hold_shares"],
                    "buy_amount": transaction["buy_amount"],
                }
            )

        for _, row in df.iterrows():
            if row["main_advice"] == "sell" and row["Ticker"] in holdings:
                sell_amount = execute_sell(
                    df,
                    row["Ticker"],
                    row["Date"],
                    holdings[row["Ticker"]]["hold_shares"],
                )
                results.append(
                    {
                        "Date": row["Date"],
                        "ticker": row["Ticker"],
                        "action": "sell",
                        "hold_shares": 0,
                        "buy_amount": 0,
                        "sell_amount": sell_amount,
                    }
                )
                del holdings[row["Ticker"]]

                # Find a new buy signal
                new_buy = df[
                    (df["Date"] == row["Date"])
                    & (df["main_advice"] == "buy")
                    & (~df["Ticker"].isin(holdings))
                ].iloc[0]
                if not new_buy.empty:
                    transaction = execute_buy(
                        df, new_buy["Ticker"], new_buy["Date"], sell_amount
                    )
                    holdings[new_buy["Ticker"]] = transaction
                    results.append(
                        {
                            "Date": new_buy["Date"],
                            "ticker": new_buy["Ticker"],
                            "action": "buy",
                            "hold_shares": transaction["hold_shares"],
                            "buy_amount": transaction["buy_amount"],
                        }
                    )

        return pd.DataFrame(results)
