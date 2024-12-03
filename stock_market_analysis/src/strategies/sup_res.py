from typing import TypeVar

import numpy as np
import pandas as pd
from scipy.signal import argrelextrema

from stock_market_analysis.src.strategies.base import BaseStrategy


Self = TypeVar("Self", bound="SupportResistanceStrategy")


class SupportResistanceStrategy(BaseStrategy):
    """Strategy based on RSI Indicator."""

    def find_support_resistance(self: Self, data: pd.DataFrame, window: int = 50):
        """Find support (local minima) and resistance (local maxima) levels in price data.

        Args:
        ----
            data (pd.Series): Stock data from yf.download()
            window (int): Window size for finding local minima/maxima.


        Returns:
        -------
            tuple: Lists of support levels (indices and values), resistance levels.
        """
        prices = data["Close"]
        local_min = argrelextrema(prices.values, np.less, order=window)[0]
        local_max = argrelextrema(prices.values, np.greater, order=window)[0]

        support = [(idx, prices[idx]) for idx in local_min]
        resistance = [(idx, prices[idx]) for idx in local_max]

        return support, resistance

    def apply(self: Self, data: pd.DataFrame):
        """Apply RSI strategy to data."""
        window = 5
        tolerance = 0.01

        support, resistance = self.find_support_resistance(data, window)

        prices = data["Close"]
        signals = ["neutral"] * len(prices)
        scores = [0] * len(prices)

        for i, price in enumerate(prices):
            # Check for proximity to support levels
            for s_idx, s_price in support:
                if abs(price - s_price) / s_price <= tolerance and i >= s_idx:
                    strength = 1 / (
                        abs(price - s_price) / s_price + 1e-6
                    )  # Stronger if closer
                    signals[i] = "buy"
                    scores[i] = max(scores[i], strength)  # Keep strongest buy score

            # Check for proximity to resistance levels
            for r_idx, r_price in resistance:
                if abs(price - r_price) / r_price <= tolerance and i >= r_idx:
                    strength = -1 / (
                        abs(price - r_price) / r_price + 1e-6
                    )  # Stronger if closer
                    signals[i] = "sell"
                    scores[i] = min(scores[i], strength)  # Keep strongest sell score

        data["sup_res_advice"] = signals
        data["sup_res_score"] = scores
