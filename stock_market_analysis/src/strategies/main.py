from typing import TypeVar

import pandas as pd

from stock_market_analysis.src.strategies.base import BaseStrategy


Self = TypeVar("Self", bound="MainAdviceScoreStrategy")


class MainAdviceScoreStrategy(BaseStrategy):
    """Base class for all BBOverupperUnderlower-based strategies."""

    def apply(self: Self, data: pd.DataFrame):
        """Calculate the main advice based on weighted indicator."""
        weights = self.kwargs["advice_weights"]
        buy_score_threshold = self.kwargs["buy_score_threshold"]
        sell_score_threshold = self.kwargs["buy_score_threshold"]
        # Compute weighted score for each row based on provided weights
        data["main_advice_score"] = sum(
            weight * data[column] for column, weight in weights.items()
        )

        # Convert score to final advice
        data["main_advice"] = data["main_advice_score"].apply(
            lambda score: "buy"
            if score > buy_score_threshold
            else "sell"
            if score < -sell_score_threshold
            else "hold"
        )

        data["main_advice_score"] = data["main_advice_score"].abs()
        return data
