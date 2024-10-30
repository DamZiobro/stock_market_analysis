from typing import Optional, TypeVar

import pandas as pd

from stock_market_analysis.src.indicators.technical_indicators import rsi
from stock_market_analysis.src.strategies.base import BaseStrategy


Self = TypeVar("Self", bound="RSIOverboughtOversoldStrategy")

RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30


def categorize_rsi(
    rsi: float,
    oversold_thresholds: Optional[tuple[int, int]] = (
        0,
        RSI_OVERSOLD,
    ),
    overbought_thresholds: Optional[tuple[int, int]] = (
        RSI_OVERBOUGHT,
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


class RSITrendBasedStrategy(BaseStrategy):
    """Strategy based on RSI Indicator."""

    def _get_rsi_advice(self: Self, row: pd.Series) -> str:
        """Generate RSI advice based on trend and RSI thresholds."""
        if row["trend"] == "uptrend" or row["trend"] == "sideways":
            if row["rsi"] < RSI_OVERSOLD:
                # Strong buy signal, closer to -1 as it approaches lower levels
                return min(1, (RSI_OVERSOLD - row["rsi"]) / RSI_OVERSOLD)
            if row["rsi"] > RSI_OVERBOUGHT:
                # Strong sell signal, closer to -1 as it approaches higher levels
                return max(-1, -(row["rsi"] - RSI_OVERBOUGHT) / (100 - RSI_OVERBOUGHT))
            return 0  # Neutral region

        if row["trend"] == "downtrend":
            if row["rsi"] > RSI_OVERSOLD:
                # Strong sell signal as it nears overbought conditions
                return max(-1, -(row["rsi"] - RSI_OVERSOLD) / RSI_OVERSOLD)
            return 0  # Neutral region
        return None

    def apply(self: Self, data: pd.DataFrame):
        """Apply RSI strategy to data."""
        data["rsi"] = rsi(data)
        data["rsi_advice"] = data.apply(self._get_rsi_advice, axis=1)
