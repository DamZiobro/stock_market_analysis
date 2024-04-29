"""Fetching data from yahoo finance."""

from datetime import datetime, timedelta, timezone
from typing import List

from yfinance import Ticker


def fetch_historical_data(stock_symbol: str, days: int = 15) -> List[float]:
    """Fetch historical closing prices for a given stock symbol over the specified number of days.

    Args:
    ----
        stock_symbol (str): The stock ticker symbol for which to fetch data.
        days (int): Number of days to fetch historical data for.

    Returns:
    -------
        List[float]: List of historical closing prices.
    """
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    ticker = Ticker(stock_symbol)
    hist = ticker.history(start=start_date, end=end_date)
    return hist["Close"].tolist()
