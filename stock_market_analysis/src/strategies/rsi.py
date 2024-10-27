from typing import Optional, TypeVar

import pandas as pd

from stock_market_analysis.src.indicators.technical_indicators import rsi
from stock_market_analysis.src.strategies.base import BaseStrategy


Self = TypeVar("Self", bound="RSIOverboughtOversoldStrategy")

DEFAULT_RSI_OVERBOUGHT_THRESHOLD = 70
DEFAULT_RSI_OVERSOLD_THRESHOLD = 30


def categorize_rsi(
    rsi: float,
    oversold_thresholds: Optional[tuple[int, int]] = (
        0,
        DEFAULT_RSI_OVERSOLD_THRESHOLD,
    ),
    overbought_thresholds: Optional[tuple[int, int]] = (
        DEFAULT_RSI_OVERBOUGHT_THRESHOLD,
        100,
    ),
):
    """Retrieve RSI category."""
    overbought_threshold_low, overbought_threshold_high = overbought_thresholds
    oversold_threshold_low, oversold_threshold_high = oversold_thresholds
    if overbought_threshold_low < rsi < overbought_threshold_high:
        return "overbought"
    if oversold_threshold_low < rsi < oversold_threshold_high:
        return "oversold"
    return "neutral"


class RSIOverboughtOversoldStrategy(BaseStrategy):
    """Strategy based on RSI Indicator."""

    def apply(self: Self, data: pd.DataFrame):
        """Apply RSI strategy to data."""
        data["rsi"] = rsi(data)
        data["rsi_meaning"] = data["rsi"].apply(categorize_rsi, **self.kwargs)

        data["rsi_advice"] = "neutral"
        data.loc[data["rsi_meaning"] == "oversold", "rsi_advice"] = "buy"
        data.loc[data["rsi_meaning"] == "overbought", "rsi_advice"] = "sell"
