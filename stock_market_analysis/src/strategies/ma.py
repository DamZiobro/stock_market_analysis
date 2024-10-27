from typing import TypeVar

import pandas as pd

from stock_market_analysis.src.indicators.technical_indicators import moving_average
from stock_market_analysis.src.strategies.base import BaseStrategy


Self = TypeVar("Self", bound="MovingAverageTrandDirectionStrategy")


class MovingAverageTrandDirectionStrategy(BaseStrategy):
    """Base class for all BBOverupperUnderlower-based strategies."""

    def apply(self: Self, data: pd.DataFrame):
        """Apply strategy to data."""
        super().apply(data)

        term = self.kwargs.get("term") or "short"

        short_ma = 20
        long_ma = 50
        if term == "long":
            short_ma = 50
            long_ma = 200

        data[f"MA_{short_ma}"] = moving_average(
            data, window=short_ma
        )  # 20-day moving average
        data[f"MA_{long_ma}"] = moving_average(
            data, window=long_ma
        )  # 50-day moving average

        # Create bb_meaning column
        data[f"ma_trend_{term}"] = "neutral"
        data.loc[
            data[f"MA_{short_ma}"] > data[f"MA_{long_ma}"], f"ma_trend_{term}"
        ] = "buy"
        data.loc[
            data[f"MA_{short_ma}"] < data[f"MA_{long_ma}"], f"ma_trend_{term}"
        ] = "sell"
