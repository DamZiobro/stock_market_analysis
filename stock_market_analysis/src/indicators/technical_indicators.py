import sys
from typing import Optional, TypeVar

import pandas as pd
import ta

from stock_market_analysis.src.logger import logger


Self = TypeVar("Self", bound="TechnicalIndicators")


def rsi(df: pd.DataFrame) -> pd.Series:
    """Calculate RSI data series."""
    ticker = df["Ticker"].iloc[0]
    logger.info("Calculating RSI for: %s", ticker)
    return ta.momentum.RSIIndicator(df["Close"]).rsi()


def macd(df: pd.DataFrame) -> pd.Series:
    """Calculate MACD data series."""
    ticker = df["Ticker"].iloc[0]
    logger.info("Calculating MACD for: %s", ticker)
    return ta.trend.MACD(close=df["Close"]).macd()


def macd_signal(df: pd.DataFrame) -> pd.Series:
    """Calculate MACD signal line data."""
    ticker = df["Ticker"].iloc[0]
    logger.info("Calculating MACD for: %s", ticker)
    return ta.trend.MACD(close=df["Close"]).macd_signal()


def macd_hist(df: pd.DataFrame) -> pd.Series:
    """Calculate MACD histogram data."""
    ticker = df["Ticker"].iloc[0]
    logger.info("Calculating MACD for: %s", ticker)
    return ta.trend.MACD(close=df["Close"]).macd_diff()


class TechnicalIndicators:
    """Applies selected technical indicators on stock data."""

    def add_indicators(
        self: Self, df: pd.DataFrame, selected_indicators: Optional[list] = None
    ) -> pd.DataFrame:
        """Add the selected technical indicators to the dataframe.

        Args:
        ----
            df (pd.DataFrame): Stock data as a DataFrame
            selected_indicators (list): List of indicators to add


        Returns:
        -------
            pd.DataFrame: DataFrame with selected technical indicators
        """
        if selected_indicators is None:
            return df

        # Get all functions from the current module
        current_module = sys.modules[__name__]
        indicator_functions = {
            name: func
            for name, func in current_module.__dict__.items()
            if callable(func) and func.__module__ == __name__
        }

        # Apply selected indicators
        for indicator in selected_indicators:
            if indicator in indicator_functions:
                df[indicator] = indicator_functions[indicator](df)
            else:
                msg = f"Warning: Indicator '{indicator}' not found in available functions."
                raise ValueError(msg)
        return df
