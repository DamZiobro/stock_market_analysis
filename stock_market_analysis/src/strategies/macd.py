from typing import TypeVar

import pandas as pd

from stock_market_analysis.src.indicators.technical_indicators import (
    macd,
    macd_hist,
    macd_signal,
)
from stock_market_analysis.src.strategies.base import BaseStrategy


Self = TypeVar("Self", bound="MACDDay3BuyDay3SellStrategy")


def find_and_apply_macd_days_signal(data: pd.DataFrame):
    """Retrieve Buy/Sell signal based on the MACD Days Rule."""
    data["macd_hist_diff"] = data["macd_hist"].diff()

    data["macd_advice"] = "neutral"
    # Buy signal: 3 consecutive days of negative but growing histogram values
    buy_condition = (
        (data["macd_hist"] < 0)
        & (data["macd_hist_diff"] > 0)
        & (data["macd_hist_diff"].shift(1) > 0)
        & (data["macd_hist_diff"].shift(2) > 0)
    )

    # Sell signal: 3 consecutive days of declining histogram values (regardless of sign)
    sell_condition = (
        (data["macd_hist_diff"] < 0)
        & (data["macd_hist_diff"].shift(1) < 0)
        & (data["macd_hist_diff"].shift(2) < 0)
    )

    data.loc[buy_condition, "macd_advice"] = "buy"
    data.loc[sell_condition, "macd_advice"] = "sell"


class MACDDay3BuyDay3SellStrategy(BaseStrategy):
    """Strategy based on RSI Indicator."""

    def apply(self: Self, data: pd.DataFrame):
        """Apply RSI strategy to data."""
        data["macd"] = macd(data)
        data["macd_signal"] = macd_signal(data)
        data["macd_hist"] = macd_hist(data)

        find_and_apply_macd_days_signal(data)


class MACDTrendBasedAdviceStrategy(BaseStrategy):
    """Strategy based on RSI Indicator."""

    def _get_macd_advice(self: Self, row: pd.Series) -> str:
        """Generate MACD advice based on trend and MACD crossover."""
        macd_diff = row["macd"] - row["macd_signal"]
        if row["trend"] == "uptrend" or row["trend"] == "sideways":
            # Positive difference indicates a buy signal, scaled by the difference
            return (
                min(1, macd_diff / (abs(row["macd_signal"]) + 1e-5))
                if macd_diff > 0
                else max(-1, macd_diff / (abs(row["macd_signal"]) + 1e-5))
            )
        if row["trend"] == "downtrend":
            # Negative difference indicates a sell signal in a downtrend
            return (
                max(-1, macd_diff / (abs(row["macd_signal"]) + 1e-5))
                if macd_diff < 0
                else 0
            )
        return None

    def apply(self: Self, data: pd.DataFrame):
        """Apply RSI strategy to data."""
        data["macd"] = macd(data)
        data["macd_signal"] = macd_signal(data)

        data["macd_advice"] = data.apply(self._get_macd_advice, axis=1)
