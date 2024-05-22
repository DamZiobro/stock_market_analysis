"""Fetching data from yahoo finance."""

from datetime import datetime, timedelta, timezone
from typing import List, Optional

import numpy as np
import pandas as pd
import yfinance as yf
from yfinance import Ticker


def fetch_close_prices(ticker: str, days: int = 15) -> List[float]:
    """Fetch historical closing prices for a given stock symbol over the specified number of days.

    Args:
    ----
        ticker (str): The stock ticker symbol for which to fetch data.
        days (int): Number of days to fetch historical data for.

    Returns:
    -------
        List[float]: List of historical closing prices.
    """
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    ticker_obj = Ticker(ticker)
    hist = ticker_obj.history(start=start_date, end=end_date)
    return hist["Close"].tolist()


def fetch_close_price(ticker: str, date: datetime) -> Optional[float]:
    """Fetch the closing price of a stock for a specific date.

    Args:
    ----
        ticker (str): The stock symbol to fetch data for, e.g., 'AAPL'.
        date (datetime): The date for which to fetch the closing price.

    Returns:
    -------
        Optional[float]: The closing price of the stock on the given date, or None.

    Raises:
    ------
        ValueError: If the date is in the future.
    """
    if date.date() > datetime.now(timezone.utc).date():
        msg = "Date cannot be in the future."
        raise ValueError(msg)

    start_date = date - timedelta(days=1)
    end_date = date + timedelta(days=1)
    data = yf.download(
        ticker, start=start_date.strftime("%Y-%m-%d"), end=end_date.strftime("%Y-%m-%d")
    )
    ticker_obj = Ticker(ticker)
    data = ticker_obj.history(start=start_date, end=end_date)

    try:
        return data["Close"].iloc[0]
    except IndexError:
        return None


def fetch_historic_dividends(ticker: str, limit: int = 10) -> Optional[pd.DataFrame]:
    """Fetch the historical dividend data for a given stock ticker.

    orders it by date with the latest first,
    and merges it with the share prices on the ex-dividend date and the day before.

    Args:
    ----
         ticker (str): The ticker symbol of the stock (e.g., 'AAPL').
         limit (int, optional): Maximum number of dividend entries to return. Default is 10.

    Returns:
    -------
        Optional[pd.DataFrame]: A DataFrame containing the dividend data merged with share prices,
                        sorted by date with the latest first, or None if there is no dividend data.

    Retrieves the dividends data and historical prices using the Ticker object's
    `dividends` and `history` properties.
    """
    stock = yf.Ticker(ticker)
    dividends = stock.dividends
    if dividends.empty:
        return None

    if limit is not None:
        dividends = dividends.tail(limit)

    dividends = dividends.reset_index(name="Dividend").rename(
        columns={"Date": "Ex-Date"}
    )
    dividends["Company code"] = ticker
    dividends["Day Before Ex-Date"] = pd.to_datetime(dividends["Ex-Date"], utc=True)
    dividends["Ex-Date"] = pd.to_datetime(
        dividends["Ex-Date"], utc=True
    ) + pd.Timedelta(days=1)

    all_dates = dividends["Ex-Date"].tolist() + dividends["Day Before Ex-Date"].tolist()
    prices = yf.download(
        ticker,
        start=min(all_dates) - timedelta(days=60),
        end=max(all_dates) + timedelta(days=1),
        progress=False,
    )
    prices.index = (
        prices.index.tz_localize("UTC")
        if prices.index.tzinfo is None
        else prices.index.tz_convert("UTC")
    )

    prices = prices.ffill()

    needed_dates = pd.date_range(
        start=min(all_dates) - timedelta(days=1), end=max(all_dates), freq="D", tz="UTC"
    )
    prices = prices.reindex(needed_dates, method="ffill")
    prices.index = prices.index.normalize()

    # Normalize the dates to ensure compatibility
    dividends["Ex-Date"] = dividends["Ex-Date"].dt.normalize()
    dividends["Day Before Ex-Date"] = dividends["Day Before Ex-Date"].dt.normalize()

    # Attempt to get the prices for the required dates and handle if they are not present
    ex_date_prices = prices.loc[
        prices.index.intersection(dividends["Ex-Date"]), ["Close"]
    ].rename(columns={"Close": "Ex-Date Price"})
    day_before_prices = prices.loc[
        prices.index.intersection(dividends["Day Before Ex-Date"]), ["Close"]
    ].rename(columns={"Close": "Day Before Price"})

    # Only merge rows where price data exists
    dividends = dividends.merge(
        ex_date_prices, left_on="Ex-Date", right_index=True, how="left"
    )
    dividends = dividends.merge(
        day_before_prices, left_on="Day Before Ex-Date", right_index=True, how="left"
    )

    # Filter out any rows that did not find matching price data
    dividends = dividends.dropna(subset=["Ex-Date Price", "Day Before Price"])

    # Filter out any rows that did not find matching price data
    dividends = dividends.dropna(subset=["Ex-Date Price", "Day Before Price"])

    return dividends.sort_values("Ex-Date", ascending=False)


def calculate_moving_average(data: pd.DataFrame, window: int) -> pd.DataFrame:
    """Calculate the moving average and its slope for the provided data.

    Args:
    ----
        data (pd.DataFrame): The data containing stock prices.
        window (int): The window size for calculating the moving average.

    Returns:
    -------
        pd.DataFrame: The input data enhanced with the moving average and its slope.
    """
    # Calculate the simple moving average (SMA)
    data["SMA"] = data["Close"].rolling(window=window).mean()
    # Calculate the slope of the moving average
    data["SMA_slope"] = data["SMA"].diff() / window
    return data


def fetch_chart_trend(ticker: str, days: int = 90, window: int = 30):
    """Get the stock price trend and its duration for the specified ticker over the last N days.

    Args:
    ----
    - ticker (str): The ticker symbol of the stock (e.g., 'AAPL').
    - days (int): Number of days to consider for the trend analysis.
    - window (int): The window size for calculating the moving average.


    Returns:
    -------
    - dict: Dictionary containing the trend direction ('up', 'down', 'flat') and duration in days.
    """
    # Fetch historical data from Yahoo Finance
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(
        days=days * 2
    )  # fetch more data to ensure enough for moving average calculation
    data = yf.download(ticker, start=start_date, end=end_date, progress=False)

    if data.empty:
        return pd.DataFrame(
            {"Error": ["No data fetched"]}
        )  # Return an empty DataFrame with an error message

    # Calculate the moving average and the slope
    data = calculate_moving_average(data, window)

    # Drop rows where SMA or SMA_slope could not be calculated due to insufficient data
    data = data.dropna(subset=["SMA", "SMA_slope"])

    # Determine the current trend direction based on the latest SMA slope
    trend_direction = "up" if data["SMA_slope"].iloc[-1] > 0 else "down"

    # Calculate the duration of the current trend
    trend_duration = 0
    current_slope_sign = np.sign(
        data["SMA_slope"].iloc[-1]
    )  # Use .iloc for position-based indexing
    reversed_slopes = data["SMA_slope"].iloc[
        ::-1
    ]  # Reverse the series using .iloc slicing
    for slope in reversed_slopes:
        if np.sign(slope) == current_slope_sign:
            trend_duration += 1
        else:
            break

    # Return the results as a DataFrame
    return pd.DataFrame(
        {
            "Company code": [ticker],
            "Trend Direction": [trend_direction],
            "Trend Duration (days)": [trend_duration],
        }
    )
