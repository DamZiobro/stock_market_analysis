"""Fetching data from yahoo finance."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional

import numpy as np
import pandas as pd
import yfinance as yf
from joblib import Parallel, delayed
from pydantic import NonNegativeInt, constr
from yfinance import Ticker

from stock_market_analysis.src.logger import logger
from stock_market_analysis.src.utils import cache_to_pickle, yf_download


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
    data = yf_download(
        ticker, start=start_date.strftime("%Y-%m-%d"), end=end_date.strftime("%Y-%m-%d")
    )
    ticker_obj = Ticker(ticker)
    data = ticker_obj.history(start=start_date, end=end_date)

    try:
        return data["Close"].iloc[0]
    except IndexError:
        return None


@cache_to_pickle(Path("/tmp/cache/dividends"))  # noqa: S108
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
    prices = yf_download(
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


def calculate_rsi(data: pd.DataFrame, window: Optional[int] = 14):
    """Calculate the Relative Strength Index (RSI).

    Args:
    ----
        data (pd.DataFrame): DataFrame containing list of List of stock prices.

    Returns:
    -------
        float: RSI value.
    """
    delta = data["Adj Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def calculate_macd(
    data: pd.DataFrame,
    short_window: Optional[int] = 12,
    long_window: Optional[int] = 26,
    signal_window: Optional[int] = 9,
):
    """Calculate the MACD (Moving Average Convergence Divergence).

    Args:
    ----
        data (pd.DataFrame): DataFrame containing list of List of stock prices.
        short_window (int): short window of MACD calculation
        long_window (int): long window of MACD calculation
        singal_window (int): signal window of MACD calculation

    Returns:
    -------
        float: MACD value.
    """
    short_ema = data["Adj Close"].ewm(span=short_window, adjust=False).mean()
    long_ema = data["Adj Close"].ewm(span=long_window, adjust=False).mean()
    macd = short_ema - long_ema
    signal = macd.ewm(span=signal_window, adjust=False).mean()
    macd_diff = macd - signal
    return macd, signal, macd_diff


def calculate_bollinger_bands(
    data: pd.DataFrame, window: Optional[int] = 20, num_std: Optional[int] = 2
):
    """Calculate Bollinger Bands.

    Args:
    ----
        data (pd.DataFrame): DataFrame containing list of List of stock prices.
        window (int): window of Bollinger Brands calculation
        num_std (int): num_std of Bolinger Brands calculation

    Returns:
    -------
        float: Bollinger Bands value.
    """
    rolling_mean = data["Adj Close"].rolling(window=window).mean()
    rolling_std = data["Adj Close"].rolling(window=window).std()
    upper_band = rolling_mean + (rolling_std * num_std)
    lower_band = rolling_mean - (rolling_std * num_std)
    return upper_band, lower_band


# @cache_to_pickle(Path("/tmp/cache/momentum"))
def fetch_momentum_analysis_single(
    ticker: str, lookback_days: int = 10, lookup_yield: float = 5.0
):
    """Perform an enhanced momentum analysis using various technical indicators.

    to calculate the probability of a 5% price gain over the next 10 days after a
    momentum signal is detected.

    The function fetches stock data for the last 6 months and calculates several
    technical indicators: Relative Strength Index (RSI), Moving Averages (MA),
    MACD, and Bollinger Bands. Based on these indicators, a momentum signal is
    generated. The function then performs a historical analysis to determine how
    often a momentum signal led to a 5% gain in the next 10 days.

    Args:
    ----
        ticker (str): The stock symbol to analyze (e.g., 'AAPL').
        lookback_days (int, optional): The number of days to look ahead when checking for
                                  price gains. Defaults to 10.
        lookup_yield (float, optional): yield of probablitity we look for. Defaults to 5.

    Returns:
    -------
        float: The probability (in percentage) of achieving a 5% price gain within
               10 days after a momentum signal.

    Raises:
    ------
        ValueError: If the stock data cannot be fetched or if the calculations fail.
    """
    oversold_signal_rsi = 30  # oversold RSI (< 30) are a BUY SIGNAL
    error_df = pd.DataFrame(
        {
            "Company code": [ticker],
            "Buy Probability": [0],
        }
    )
    # Fetch stock data
    try:
        if ticker in ["88 Energy Ltd.L", "First Tin.L", "GTE.L"]:
            return error_df
        stock_data = yf_download(ticker, period="6mo", interval="1d")
        # exclude some tickers
    except Exception:
        logger.exception(f"ERROR: Exception for ticker: {ticker}:")
        return error_df

    # Calculate RSI (Relative Strength Index)
    rsi_df = calculate_rsi(stock_data)
    stock_data["RSI"] = rsi_df

    recent_rsi = None
    if len(rsi_df) > 1:
        recent_rsi = rsi_df.iloc[-1]
        print(recent_rsi)

    # Calculate short-term and long-term Moving Averages
    stock_data["MA_10"] = stock_data["Adj Close"].rolling(window=10).mean()
    stock_data["MA_50"] = stock_data["Adj Close"].rolling(window=50).mean()

    # Calculate MACD (Moving Average Convergence Divergence)
    stock_data["MACD"], stock_data["Signal"], stock_data["MACD_Diff"] = calculate_macd(
        stock_data
    )

    # Calculate Bollinger Bands
    stock_data["Upper_Band"], stock_data["Lower_Band"] = calculate_bollinger_bands(
        stock_data
    )

    # Define momentum signals
    stock_data["Momentum Signal"] = np.where(
        (stock_data["RSI"] < oversold_signal_rsi),
        # & (stock_data["MA_10"] > stock_data["MA_50"]),
        # & (stock_data["MACD_Diff"] > 0)
        # & (stock_data["Adj Close"] < stock_data["Lower_Band"]),
        1,
        0,
    )

    # Historical analysis: Check how often a momentum signal led to 5% gain in next 10 days
    win_count = 0
    signal_count = 0

    for i in range(len(stock_data) - lookback_days):
        if stock_data["Momentum Signal"].iloc[i] == 1:
            signal_count += 1
            future_price = stock_data["Adj Close"].iloc[i + lookback_days]
            current_price = stock_data["Adj Close"].iloc[i]
            price_change = ((future_price - current_price) / current_price) * 100
            if price_change >= lookup_yield:
                win_count += 1

    # Calculate probability of gaining 5% in the next 10 days after a momentum signal
    probability = win_count / signal_count * 100 if signal_count > 0 else 0

    logger.info(
        "momentum_analysis: ticker: %s; probability: %s; signal_count: %s; win_count: %s",
        ticker,
        str(probability),
        signal_count,
        win_count,
    )
    # return round(probability, 2)
    # Return the results as a DataFrame
    return pd.DataFrame(
        {
            "Company code": [ticker],
            "Signal Count": [signal_count],
            "Win Count": [win_count],
            "RSI": [recent_rsi],
            # "MA_10": [stock_data["MA_10"]],
            # "MA_50": [stock_data["MA_50"]],
            # "MACD_Diff": [stock_data["MACD_Diff"]],
            # "BB_Upper_Band": [stock_data["Upper_Band"]],
            # "BB_Lower_Band": [stock_data["Lower_Band"]],
            "Buy Probability": [round(probability, 2)],
        }
    )


def fetch_momentum_analysis(
    tickers: list[str], lookback_days: int = 10, lookup_yield: float = 5.0
):
    """Fetch stock momenum_analysis data for a list of tickers.

    and returns a DataFrame sorted by trend direction and duration.

    Args:
    ----
        tickers (list of str): List of ticker symbols.
        lookback_days (int): Number of days we look ahead when checking for price gain
        lookup_yield (int): Yield percent we look for.

    Returns:
    -------
        pd.DataFrame: A DataFrame containing the trend direction and duration for each ticker.
    """
    # Define a helper function to fetch trend for a single ticker
    def fetch_momentum_for_ticker(ticker: str) -> pd.DataFrame:
        return fetch_momentum_analysis_single(ticker, lookback_days, lookup_yield)

    # Use joblib to run fetching in parallel
    results = Parallel(n_jobs=-1)(
        delayed(fetch_momentum_for_ticker)(ticker) for ticker in tickers
    )

    # Combine all individual DataFrame results into one DataFrame
    if not results:
        return pd.DataFrame()  # Return empty DataFrame if no results

    result_df = pd.concat(results, ignore_index=True)
    # remove all columns when Buy Probability == 0
    result_df = result_df.loc[result_df["Buy Probability"] != 0]
    # filter out all rows with NaN direction (errored columns)
    result_df = result_df.sort_values(
        by=["RSI", "Buy Probability", "Signal Count", "Company code"],
        ascending=[True, False, False, True],
    )
    return result_df.reset_index(drop=True)


@cache_to_pickle(Path("/tmp/cache/trends"))  # noqa: S108
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
    data = yf_download(ticker, start=start_date, end=end_date, progress=False)

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


def fetch_chart_trends(tickers: list[str], days: int = 90, window: int = 30):
    """Fetch stock price trends for a list of tickers.

    and returns a DataFrame sorted by trend direction and duration.

    Args:
    ----
        tickers (list of str): List of ticker symbols.
        days (int): Number of days to consider for the trend analysis.
        window (int): The window size for calculating the moving average.

    Returns:
    -------
        pd.DataFrame: A DataFrame containing the trend direction and duration for each ticker.
    """
    # Define a helper function to fetch trend for a single ticker
    def fetch_trend_for_ticker(ticker: str) -> pd.DataFrame:
        return fetch_chart_trend(ticker, days, window)

    # Use joblib to run fetching in parallel
    results = Parallel(n_jobs=-1)(
        delayed(fetch_trend_for_ticker)(ticker) for ticker in tickers
    )

    # Combine all individual DataFrame results into one DataFrame
    if not results:
        return pd.DataFrame()  # Return empty DataFrame if no results

    result_df = pd.concat(results, ignore_index=True)
    # filter out all rows with NaN direction (errored columns)
    result_df = result_df.dropna(subset=["Trend Direction", "Trend Duration (days)"])
    result_df = result_df.drop(columns=["Error"])
    result_df = result_df.sort_values(
        by=["Trend Direction", "Trend Duration (days)"], ascending=[False, False]
    )
    return result_df.reset_index(drop=True)


@cache_to_pickle(Path("/tmp/cache/volume"))  # noqa: S108
def fetch_volume_analysis_data(
    ticker: constr(min_length=1), days: NonNegativeInt  # type: ignore
) -> pd.DataFrame:
    """Perform volume analysis on a given stock ticker.

    Args:
    ----
        ticker (str): Stock ticker symbol.
        days (NonNegativeInt): Number of recent days to analyze.

    Returns:
    -------
        pd.DataFrame: DataFrame containing the analysis results.
    """
    # Fetch historical data
    stock_data = yf_download(ticker, period=f"{days}d", progress=False)
    if stock_data.empty:
        return pd.DataFrame(
            {"Error": ["No data fetched"]}
        )  # Return an empty DataFrame with an error message

    # Calculate daily returns
    stock_data["Returns"] = stock_data["Close"].pct_change()

    # Analyze volume trends
    increasing_volume = (stock_data["Volume"].diff() > 0).sum()
    decreasing_volume = (stock_data["Volume"].diff() < 0).sum()
    avg_volume = stock_data["Volume"].mean()
    volume_spikes = stock_data[stock_data["Volume"] > 2 * avg_volume]

    analysis_results = {
        "Company code": ticker,
        "average_volume": avg_volume,
        "increasing_volume_days": increasing_volume,
        "decreasing_volume_days": decreasing_volume,
        "volume_spikes_count": len(volume_spikes),
    }

    return pd.DataFrame([analysis_results])


def fetch_volume_analysis_data_multiple_tickers(
    tickers: List[constr(min_length=1)], days: NonNegativeInt, n_jobs: int = -1  # type: ignore
) -> pd.DataFrame:
    """Perform volume analysis on multiple stock tickers in parallel.

    Args:
    ----
        tickers (List[str]): List of stock ticker symbols.
        days (NonNegativeInt): Number of recent days to analyze for each ticker.
        n_jobs (int): Number of jobs to run in parallel. Default is -1 (use all processors).

    Returns:
    -------
        pd.DataFrame: DataFrame containing the analysis results for all tickers.
    """
    results = Parallel(n_jobs=n_jobs)(
        delayed(fetch_volume_analysis_data)(ticker, days) for ticker in tickers
    )
    result_df = pd.concat(results, ignore_index=True)

    result_df = result_df.dropna(subset=["average_volume"])
    result_df = result_df.drop(columns=["Error"])
    result_df = result_df.sort_values(
        by=["increasing_volume_days", "average_volume", "decreasing_volume_days"],
        ascending=[False, False, False],
    )
    return result_df.reset_index(drop=True)
