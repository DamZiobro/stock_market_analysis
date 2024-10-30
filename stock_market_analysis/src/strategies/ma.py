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


class MovingAverageGetTrandDirectionStrategy(BaseStrategy):
    """Base class for all BBOverupperUnderlower-based strategies."""

    def apply(self: Self, data: pd.DataFrame):
        """Apply strategy to data."""
        super().apply(data)

        data["ma_short"] = moving_average(data, 20)
        data["ma_medium"] = moving_average(data, 50)
        data["ma_long"] = moving_average(data, 200)

        def get_trend(row: pd.Series) -> str:
            """Get trend based on row value."""
            if row["ma_short"] > row["ma_medium"] > row["ma_long"]:
                return "uptrend"
            if row["ma_short"] < row["ma_medium"] < row["ma_long"]:
                return "downtrend"
            return "sideways"

        # Apply the trend determination for each row
        data["trend"] = data.apply(get_trend, axis=1)


class MovingAverageTrendBasedStrategy(BaseStrategy):
    """Base class for all BBOverupperUnderlower-based strategies."""

    def _get_ma_short_advice(self: Self, row: pd.Series) -> str:
        """Generate short-term moving average advice based on trend."""
        ma_diff = row["ma_short"] - row["ma_medium"]
        if row["trend"] == "uptrend" or row["trend"] == "sideways":
            # Positive difference indicates a buy signal, scaled by the difference
            return (
                min(1, ma_diff / (row["ma_medium"] + 1e-5))
                if ma_diff > 0
                else max(-1, ma_diff / (row["ma_medium"] + 1e-5))
            )
        if row["trend"] == "downtrend":
            # Negative difference indicates a sell signal in a downtrend
            return max(-1, ma_diff / (row["ma_medium"] + 1e-5)) if ma_diff < 0 else 0
        return None

    def apply(self: Self, data: pd.DataFrame):
        """Apply strategy to data."""
        super().apply(data)

        data["ma_short"] = moving_average(data, 20)
        data["ma_medium"] = moving_average(data, 50)
        data["ma_short_advice"] = data.apply(self._get_ma_short_advice, axis=1)
