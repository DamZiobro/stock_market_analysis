from typing import TypeVar

import numpy as np
import pandas as pd

from stock_market_analysis.src.strategies.base import BaseStrategy


Self = TypeVar("Self", bound="SupportResistanceStrategy")


class SupportResistanceStrategy(BaseStrategy):
    """Strategy based on RSI Indicator."""

    def find_support_resistance(
        self: Self,
        data: pd.DataFrame,
        window: int = 5,
        buy_advice_min_window: int = 30,
        sell_advice_min_window: int = 30,
    ):
        """Find support (local minima) and resistance (local maxima) levels in price data.

        Args:
        ----
            data (pd.Series): Stock data from yf.download()
            min_bounce (int): Minimum number of bounces (touches) for confirmation.
            window (int): Window size for calculating price volatility.


        Returns:
        -------
            tuple: Lists of support levels (indices and values), resistance levels.
        """
        data[
            "detected_close"
        ] = np.nan  # Where we'll store the local min/max price on the confirmation day
        data["is_support"] = False
        data["is_resistance"] = False
        data["sup_res_window"] = 0
        data["sup_res_window_date"] = pd.NaT
        data["sup_res_advice"] = "hold"

        # Step 1: Identify local min/max on day i (but do not set signals yet)
        for i in range(window, len(data) - window):
            price_slice = data["Close"].iloc[i - window : i + window + 1]
            current_price = data["Close"].iloc[i]

            # Check if day i is a local minimum
            if current_price == price_slice.min():
                data.at[data.index[i], "is_support"] = True

            # Check if day i is a local maximum
            if current_price == price_slice.max():
                data.at[data.index[i], "is_resistance"] = True

        # We'll store (price, date) for each confirmed support/resistance detection day.
        support_points = []
        resistance_points = []
        data.index[0]

        # Step 2: For each local min/max day i, place the signal on day j = i + window
        #         if j is within the dataset range.
        for i in range(window, len(data) - window):
            idx_i = data.index[i]
            price_i = data["Close"].iloc[i]

            # j is the "confirmation" day
            j = i + window
            if j >= len(data):
                continue  # can't confirm if j is out of range

            idx_j = data.index[j]

            if data.at[idx_i, "is_support"]:
                # This is a local min -> We'll place the "buy" signal on day j
                # 1) See if there's a prior support with price <= price_i
                possible_matches = [(p, d) for (p, d) in support_points if p <= price_i]
                if possible_matches:
                    # pick the most recent date
                    _, last_match_date = max(possible_matches, key=lambda x: x[1])
                    sup_res_window = (idx_j - last_match_date).days
                    data.at[idx_i, "sup_res_window"] = sup_res_window
                    data.at[idx_i, "sup_res_window_date"] = last_match_date

                    data.at[idx_j, "sup_res_window"] = sup_res_window
                    data.at[idx_j, "sup_res_window_date"] = last_match_date

                    # set signals, store detection price
                    if sup_res_window > buy_advice_min_window:
                        data.at[idx_j, "sup_res_advice"] = "buy"
                        data.at[idx_j, "detected_close"] = price_i

                # Add this to the list of known supports (use the confirmation day j)
                support_points.append((price_i, idx_j))

            if data.at[idx_i, "is_resistance"]:
                # This is a local max -> We'll place the "sell" signal on day j
                possible_matches = [
                    (p, d) for (p, d) in resistance_points if p >= price_i
                ]
                if possible_matches:
                    _, last_match_date = max(possible_matches, key=lambda x: x[1])
                    sup_res_window = (idx_j - last_match_date).days * -1
                    data.at[idx_i, "sup_res_window"] = sup_res_window
                    data.at[idx_i, "sup_res_window_date"] = last_match_date

                    data.at[idx_j, "sup_res_window"] = sup_res_window
                    data.at[idx_j, "sup_res_window_date"] = last_match_date

                    # set signals, store detection price
                    if sup_res_window < sell_advice_min_window * -1:
                        data.at[idx_j, "sup_res_advice"] = "sell"
                        data.at[idx_j, "detected_close"] = price_i

                resistance_points.append((price_i, idx_j))

        return data

    def apply(self: Self, data: pd.DataFrame):
        """Apply RSI strategy to data."""
        window = 3
        buy_advice_min_window = 30
        sell_advice_min_window = 30
        data = self.find_support_resistance(data, window, buy_advice_min_window, sell_advice_min_window)
