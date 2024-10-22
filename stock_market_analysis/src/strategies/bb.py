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
