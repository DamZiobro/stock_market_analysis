from typing import TypeVar

import pandas as pd

from stock_market_analysis.src.indicators.technical_indicators import rsi
from stock_market_analysis.src.strategies.base import BaseStrategy


Self = TypeVar("Self", bound="RSIOverboughtOversoldStrategy")

RSI_OVERBOUGHT_THRESHOLD = 70
RSI_OVERSOLD_THRESHOLD = 30


def categorize_rsi(rsi: float):
    """Retrieve RSI category."""
    if rsi > RSI_OVERBOUGHT_THRESHOLD:
        return "overbought"
    if rsi < RSI_OVERSOLD_THRESHOLD:
        return "oversold"
    return "neutral"


class RSIOverboughtOversoldStrategy(BaseStrategy):
    """Strategy based on RSI Indicator."""

    def apply(self: Self, data: pd.DataFrame):
        """Apply RSI strategy to data."""
        data["rsi"] = rsi(data)
        data["rsi_category"] = data["rsi"].apply(categorize_rsi)
