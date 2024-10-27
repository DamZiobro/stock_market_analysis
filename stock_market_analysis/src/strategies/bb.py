from typing import TypeVar

import pandas as pd

from stock_market_analysis.src.indicators.technical_indicators import bb_lower, bb_upper
from stock_market_analysis.src.logger import logger
from stock_market_analysis.src.strategies.base import BaseStrategy


Self = TypeVar("Self", bound="BBOverupperUnderlowerStrategy")


class BBOverupperUnderlowerStrategyBase(BaseStrategy):
    """Base class for all BBOverupperUnderlower-based strategies."""

    def apply(self: Self, data: pd.DataFrame):
        """Apply strategy to data."""
        data["bb_lower"] = bb_lower(data)
        data["bb_upper"] = bb_upper(data)

        # Create bb_meaning column
        data["bb_meaning"] = "within_bb"
        data.loc[data["Close"] < data["bb_lower"], "bb_meaning"] = "underlower"
        data.loc[data["Close"] > data["bb_upper"], "bb_meaning"] = "overupper"

        # Create bb_diff column based on bb_meaning
        data["bb_diff_percent"] = 0.0
        data.loc[data["bb_meaning"] == "overupper", "bb_diff_percent"] = (
            (data["Close"] - data["bb_upper"]) / data["Close"] * 100
        )
        data.loc[data["bb_meaning"] == "underlower", "bb_diff_percent"] = (
            (data["Close"] - data["bb_lower"]) / data["Close"] * 100
        )
        data.loc[data["bb_meaning"] == "within_bb", "bb_diff_percent"] = data[
            ["Close", "bb_upper", "bb_lower"]
        ].apply(
            lambda row: min(
                abs(row["Close"] - row["bb_upper"]) / row["Close"] * 100,
                abs(row["Close"] - row["bb_lower"]) / row["Close"] * 100,
            ),
            axis=1,
        )


class BBOverupperUnderlowerStrategy(BBOverupperUnderlowerStrategyBase):
    """BollingerBands-based strategy.

    - 'buy' signal => when BB is lower than bb_lower
    - 'sell' signal => when BB is higher than bb_upper.
    """

    def apply(self: Self, data: pd.DataFrame):
        """Apply strategy to data."""
        super().apply(data)

        data["bb_advice"] = "neutral"
        data.loc[data["bb_meaning"] == "underlower", "bb_advice"] = "buy"
        data.loc[data["bb_meaning"] == "overupper", "bb_advice"] = "sell"


class BBOverupperUnderlowerNDaysAgoStrategy(BBOverupperUnderlowerStrategyBase):
    """BollingerBands-based strategy.

    - 'buy' signal => when BB was lower than bb_lower N days ago, but is upper later.
    - 'sell' signal => when BB was higher than bb_upper N days ago, but is lower later.
    """

    def apply(self: Self, data: pd.DataFrame):
        """Assign 'buy', 'sell', or 'neutral' to 'bb_advice' column.

        based on 'bb_meaning' column logic
        checking the bb_meaning from N days ago as specified by days_ago.
        """
        super().apply(data)

        days_ago_under = self.kwargs.get("days_ago_under") or 0
        days_ago_over = self.kwargs.get("days_ago_over") or 0
        ticker = data.iloc[0]["Ticker"]
        logger.info(
            "BBOverupperUnderlowerNDaysAgoStrategy - apply for "
            "days_ago_under: %d; days_ago_over: %d, ticker: %s",
            days_ago_under,
            days_ago_over,
            ticker,
        )
        data["bb_advice"] = "neutral"  # Default all rows to 'neutral'
        data.loc[
            (data["bb_meaning"].shift(days_ago_under) == "underlower")
            # & (data["bb_meaning"].shift(days_ago_under-1) == "within_bb")
            & (data["bb_meaning"] == "within_bb"),
            "bb_advice",
        ] = "buy"
        # for i in range(days_ago_over, 0):
        data.loc[
            (data["bb_meaning"].shift(days_ago_over) == "overupper")
            & (data["bb_meaning"] == "within_bb"),
            "bb_advice",
        ] = "sell"
