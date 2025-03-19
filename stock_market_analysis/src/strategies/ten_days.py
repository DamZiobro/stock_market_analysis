from typing import TypeVar

import numpy as np
import pandas as pd

from stock_market_analysis.src.strategies.base import BaseStrategy


Self = TypeVar("Self", bound="TenDaysLowsHighsStrategy")


class TenDaysLowsHighsStrategy(BaseStrategy):
    """Strategy based on finding 10 day lows for buy and 10 day highs for sell."""

    def add_ten_days_advice(self, df):
        """Add two columns to the DataFrame.

        - 'ten_days_advice': 'buy' if the current close is the 10-day low,
        'sell' if it's the 10-day high, 'hold' otherwise.
        - 'ten_days_score': a normalized score (between 0 and 1) based on the slope
        of the last 10 days of closing prices.
        """
        df["ten_days_advice"] = "hold"
        df["position_days"] = 0
        df["50_MA"] = df["Close"].rolling(window=50).mean()
        df["200_MA"] = df["Close"].rolling(window=200).mean()
        df["ten_days_score"] = np.nan

        position_open = False
        days_held = 0
        slopes = []

        for i in range(len(df)):
            if i < 200:  # Skip initial rows without enough data for moving averages
                slopes.append(np.nan)
                continue

            current_price = df["Close"].iloc[i]
            window_10d = df["Close"].iloc[i - 9 : i + 1]

            # Calculate slope for scoring
            x = np.arange(10)
            slope = np.polyfit(x, window_10d.values, 1)[0]
            slopes.append(slope)

            if not position_open:
                if (
                    (current_price == window_10d.min())
                    and (current_price > df["50_MA"].iloc[i])
                    and (current_price > df["200_MA"].iloc[i])
                ):
                    df.iloc[i, df.columns.get_loc("ten_days_advice")] = "buy"
                    position_open = True
                    days_held = 1
            else:
                days_held += 1
                sell_condition = (
                    (current_price == window_10d.max())
                    or (current_price < df["50_MA"].iloc[i])
                    or (days_held >= 10)
                )
                if sell_condition:
                    df.iloc[i, df.columns.get_loc("ten_days_advice")] = "sell"
                    position_open = False
                    days_held = 0
                else:
                    df.iloc[i, df.columns.get_loc("position_days")] = days_held

        # Normalize slopes for scoring
        valid_slopes = pd.Series(slopes)
        min_slope, max_slope = valid_slopes.min(), valid_slopes.max()

        if max_slope != min_slope:
            normalized_scores = (valid_slopes - min_slope) / (max_slope - min_slope)
        else:
            normalized_scores = pd.Series(0.5, index=valid_slopes.index)

        df["ten_days_score"] = normalized_scores.values

        return df

    def apply(self: Self, data: pd.DataFrame):
        """Apply 10 days lows / highs strategy to data."""
        data = self.add_ten_days_advice(data)
