from typing import TypeVar

import pandas as pd

from stock_market_analysis.src.indicators.technical_indicators import (
    macd,
    macd_hist,
    macd_signal,
)
from stock_market_analysis.src.strategies.base import BaseStrategy


Self = TypeVar("Self", bound="MACDDay3BuyDay3SellStrategy")

RSI_OVERBOUGHT_THRESHOLD = 70
RSI_OVERSOLD_THRESHOLD = 30


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
        & (data["macd_hist_diff"].shift(3) < 0)
    )

    # Sell signal: 3 consecutive days of declining histogram values (regardless of sign)
    sell_condition = (
        (data["macd_hist_diff"] < 0)
        & (data["macd_hist_diff"].shift(1) < 0)
        & (data["macd_hist_diff"].shift(2) < 0)
        & (data["macd_hist_diff"].shift(3) > 0)
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
