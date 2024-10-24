from typing import TypeVar

import pandas as pd

from stock_market_analysis.src.indicators.technical_indicators import bb_lower, bb_upper
from stock_market_analysis.src.strategies.base import BaseStrategy


Self = TypeVar("Self", bound="BBOverupperUnderlowerStrategy")


class BBOverupperUnderlowerStrategy(BaseStrategy):
    """Strategy based on Bollinger Bands indicator."""

    def apply(self: Self, data: pd.DataFrame):
        """Apply BB strategy to data."""
        data["bb_lower"] = bb_lower(data)
        data["bb_upper"] = bb_upper(data)

        # Create bb_signal column
        data["bb_signal"] = "within_bb"
        data.loc[data["Close"] < data["bb_lower"], "bb_signal"] = "underlower"
        data.loc[data["Close"] > data["bb_upper"], "bb_signal"] = "overupper"

        # Create bb_diff column based on bb_signal
        data["bb_diff_percent"] = 0.0
        data.loc[data["bb_signal"] == "overupper", "bb_diff_percent"] = (
            (data["Close"] - data["bb_upper"]) / data["Close"] * 100
        )
        data.loc[data["bb_signal"] == "underlower", "bb_diff_percent"] = (
            (data["Close"] - data["bb_lower"]) / data["Close"] * 100
        )
        data.loc[data["bb_signal"] == "within_bb", "bb_diff_percent"] = data[
            ["Close", "bb_upper", "bb_lower"]
        ].apply(
            lambda row: min(
                abs(row["Close"] - row["bb_upper"]) / row["Close"] * 100,
                abs(row["Close"] - row["bb_lower"]) / row["Close"] * 100,
            ),
            axis=1,
        )

        data["bb_advice"] = "within_bb"
        data.loc[data["Close"] < data["bb_lower"], "bb_advice"] = "buy"
        data.loc[data["Close"] > data["bb_upper"], "bb_advice"] = "sell"
