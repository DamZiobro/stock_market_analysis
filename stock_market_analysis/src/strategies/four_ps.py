from typing import TypeVar

import pandas as pd

from stock_market_analysis.src.strategies.base import BaseStrategy


Self = TypeVar("Self", bound="Phases4PSDetectionStrategy")


class Phases4PSDetectionStrategy(BaseStrategy):
    """BollingerBands-based strategy.

    - 'buy' signal => when 4PS phase is New Trend
    - 'sell' signal => when stock is 15 months after buy date
    """

    def _classify_phase(
        self: Self, row: pd.Series, prev_phase: str, Wprev_high: float, prev_low: float
    ) -> str:
        # Check for higher highs and higher lows (uptrend)
        is_higher_high = row["Close"] > prev_high
        is_higher_low = row["Close"] > prev_low

        # Phase 1: Proven Performance
        if (
            row["ma_50"] > row["ma_200"]
            and row["ma_200_slope"] > 0
            #and row["rsi"] > 50
            and is_higher_high
            and is_higher_low
        ):
            return "Phase 1: Proven Performance"

        # Phase 2: Consolidation Base
        if (
            row["Close"] < row["bb_upper"]
            and row["Close"] > row["bb_lower"]
            and abs(row["momentum_10"]) < 0.01
            and row["macd"] < row["macd_signal"]
            #and prev_phase == "Phase 1: Proven Performance"
        ):
            return "Phase 2: Consolidation Base"

        # Phase 3: Consolidation Breakout
        if (
            row["Close"] > row["bb_upper"]
            and row["macd"] > row["macd_signal"]
            #and prev_phase == "Phase 2: Consolidation Base"
        ):
            return "Phase 3: Consolidation Breakout"

        # Phase 4: New Trend
        if (
            row["Close"] > row["ma_50"] > row["ma_200"]
            and row["ma_50_slope"] > 0
            and row["momentum_10"] > 0.02
            #and prev_phase == "Phase 3: Consolidation Breakout"
        ):
            return "new_trend"

        # Default case
        return "Undefined"

    def apply(self: Self, data: pd.DataFrame):
        """Apply strategy to data."""
        super().apply(data)

        # Initialize the phase column
        data["4ps_phase"] = "Undefined"

        prev_phase = "Undefined"
        prev_high = data["Close"].iloc[0]
        prev_low = data["Close"].iloc[0]

        # Apply phase classification row by row
        for idx, row in data.iterrows():
            current_phase = self._classify_phase(row, prev_phase, prev_high, prev_low)
            data.at[idx, "phase"] = current_phase

            # Update previous high and low
            if current_phase in ["Phase 1: Proven Performance", "new_trend"]:
                prev_high = max(prev_high, row["Close"])
                prev_low = min(prev_low, row["Close"])

            prev_phase = current_phase

        data["4ps_advice"] = data["4ps_phase"].apply(
            lambda phase: "buy" if phase == "new_trend" else "neutral"
        )
