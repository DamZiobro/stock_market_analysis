"""Fetching data from yahoo finance."""

from datetime import datetime, timedelta, timezone
from typing import List, Optional

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

    # If a limit is set, truncate the dividends DataFrame to that limit
    if limit is not None:
        dividends = dividends.tail(limit)

    dividends = dividends.reset_index(name="Dividend").rename(
        columns={"Date": "Ex-Date"}
    )
    dividends["Day Before Ex-Date"] = dividends["Ex-Date"] - timedelta(days=1)

    # Fetch historical prices for the required dates
    all_dates = dividends["Ex-Date"].tolist() + dividends["Day Before Ex-Date"].tolist()
    prices = stock.history(
        start=min(all_dates) - timedelta(days=30),
        end=max(all_dates) + timedelta(days=1),
    )

    # Make sure to reindex the prices pd.DataFrame to fill missing dates
    idx = pd.date_range(start=min(all_dates) - timedelta(days=1), end=max(all_dates))
    prices = prices.reindex(
        idx, method="pad"
    )  # Use forward fill to carry last known prices forward

    # Create sub-DataFrames for ex-date and day before, then merge them
    ex_date_prices = prices.loc[dividends["Ex-Date"], ["Close"]].rename(
        columns={"Close": "Ex-Date Price"}
    )
    day_before_prices = prices.loc[dividends["Day Before Ex-Date"], ["Close"]].rename(
        columns={"Close": "Day Before Price"}
    )
    dividends = dividends.merge(
        ex_date_prices, left_on="Ex-Date", right_index=True, how="left"
    )
    dividends = dividends.merge(
        day_before_prices, left_on="Day Before Ex-Date", right_index=True, how="left"
    )

    # Sort the final DataFrame by ex-dividend date, newest first
    return dividends.sort_values("Ex-Date", ascending=False)
