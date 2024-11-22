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


def bb_upper(df: pd.DataFrame) -> pd.Series:
    """Calculate MACD data series."""
    ticker = df["Ticker"].iloc[0]
    logger.info("Calculating BollingerBands Upper: %s", ticker)
    return ta.volatility.BollingerBands(
        close=df["Close"], window=20, window_dev=2
    ).bollinger_hband()


def bb_lower(df: pd.DataFrame) -> pd.Series:
    """Calculate MACD data series."""
    ticker = df["Ticker"].iloc[0]
    logger.info("Calculating BollingerBands Lower: %s", ticker)
    return ta.volatility.BollingerBands(
        close=df["Close"], window=20, window_dev=2
    ).bollinger_lband()


def moving_average(df: pd.DataFrame, window: int) -> pd.Series:
    """Calculate moving average data."""
    ticker = df["Ticker"].iloc[0]
    logger.info("Calculating Moving Average for: %s with window: %d", ticker, window)
    return df["Close"].rolling(window=window).mean()


def volume_ma(df: pd.DataFrame, window: int) -> pd.Series:
    """Calculate moving average data."""
    ticker = df["Ticker"].iloc[0]
    logger.info("Calculating Moving Average for: %s with window: %d", ticker, window)
    return df["Volume"].rolling(window=window).mean()


def ma_20(df: pd.DataFrame) -> pd.Series:
    """Calculate moving_average with window=20."""
    return moving_average(df, window=20)


def ma_50(df: pd.DataFrame) -> pd.Series:
    """Calculate moving_average with window=50."""
    return moving_average(df, window=50)


def ma_200(df: pd.DataFrame) -> pd.Series:
    """Calculate moving_average with window=200."""
    return moving_average(df, window=200)


def ma_20_slope(df: pd.DataFrame) -> pd.Series:
    """Calculate slope moving_average with window=20."""
    return df["ma_20"].diff()


def ma_50_slope(df: pd.DataFrame) -> pd.Series:
    """Calculate slope moving_average with window=20."""
    return df["ma_50"].diff()


def ma_200_slope(df: pd.DataFrame) -> pd.Series:
    """Calculate slope moving_average with window=20."""
    return df["ma_200"].diff()


def volume_ma_20(df: pd.DataFrame) -> pd.Series:
    """Calculate volume moving_average with window=20."""
    return volume_ma(df, window=20)


def momentum(df: pd.DataFrame, window: int) -> pd.Series:
    """Calculate momentum (percentage price change over last 10 days)."""
    ticker = df["Ticker"].iloc[0]
    logger.info("Calculating momentum for: %s with window: %d", ticker, window)
    return df["Close"].pct_change(periods=window)


def momentum_10(df: pd.DataFrame) -> pd.Series:
    """Calculate momentum (percentage price change over last 10 days)."""
    return momentum(df, window=10)


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
