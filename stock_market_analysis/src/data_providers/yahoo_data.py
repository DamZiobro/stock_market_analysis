"""Provider of data from Yahoo Finance service."""
from pathlib import Path
from typing import TypeVar

import pandas as pd
import yfinance as yf

from stock_market_analysis.src.data_providers.base_provider import BaseDataProvider
from stock_market_analysis.src.logger import logger
from stock_market_analysis.src.utils.utils import EMPTY_DF, cache_to_pickle


Self = TypeVar("Self", bound="YahooDataProvider")


@cache_to_pickle(Path("/tmp/cache/yf_download"))  # noqa: S108
def yf_download(ticker: str, period: str) -> pd.DataFrame:
    """Fetch data for a single ticker within the specified period.

    Args:
    ----
        ticker (str): Stock ticker symbol
        period (Union[str, None]): Time period for data (e.g., '1y', '2023-01-01:2024-01-01')

    Returns:
    -------
        Dict: Stock data as a dictionary
    """
    logger.info(
        "Downloading Yahoo Finance history data for: ticker: %s; period: %s",
        ticker,
        period,
    )
    if ":" in period:
        start, end = period.split(":")
        data = yf.download(ticker, start=start, end=end, progress=False)
    else:
        data = yf.download(ticker, period=period, progress=False)

    data.columns = data.columns.get_level_values(0)
    return data


class YahooDataProvider(BaseDataProvider):
    """Fetches stock data from Yahoo Finance."""

    def get_data(self: Self, ticker: str, period: str) -> pd.DataFrame:
        """Fetch data for a single ticker within the specified period.

        Args:
        ----
            ticker (str): Stock ticker symbol
            period (Union[str, None]): Time period for data (e.g., '1y', '2023-01-01:2024-01-01')

        Returns:
        -------
            Dict: Stock data as a dictionary
        """
        try:
            return yf_download(ticker, period)
        except Exception as ex:
            logger.error(
                "ERROR: cannot download data for ticker: %s; period: %s; msg: %s",
                ticker,
                period,
                str(ex),
            )
            return EMPTY_DF
