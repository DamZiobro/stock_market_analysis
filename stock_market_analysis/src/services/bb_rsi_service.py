from typing import ClassVar, TypeVar

import pandas as pd

from stock_market_analysis.src.analysis.filtering import FilterBy
from stock_market_analysis.src.analysis.sorting import SortBy
from stock_market_analysis.src.data_providers.yahoo_data import YahooDataProvider
from stock_market_analysis.src.services.base_service import BaseAnalysisService
from stock_market_analysis.src.strategies.bb import (
    BBOverupperUnderlowerNDaysAgoStrategy,
)
from stock_market_analysis.src.strategies.ma import MovingAverageTrandDirectionStrategy
from stock_market_analysis.src.strategies.rsi import RSIOverboughtOversoldStrategy


Self = TypeVar("Self", bound="BBAndRSIAndMAService")


class BBAndRSIAndMAService(BaseAnalysisService):
    """Facade service for stock market analysis.

    Backtested 1 year from 27.10.2024 this strategy gave 10% gain
    """

    data_provider: ClassVar = YahooDataProvider()  # type: ignore
    technical_indicators: ClassVar = ["rsi", "bb_lower", "bb_upper"]
    pre_run_strategies: ClassVar = [
        RSIOverboughtOversoldStrategy(
            oversold_thresholds=(20, 35), overbought_thresholds=(65, 100)
        ),
        # BBOverupperUnderlowerStrategy(),
        BBOverupperUnderlowerNDaysAgoStrategy(days_ago_under=1, days_ago_over=1),
        MovingAverageTrandDirectionStrategy(term="short"),
        # apply only for sideways markets
        # add another exit strategy (ex. 3 days macd declining) - see Burberry
        # include moving averages?
    ]  # type: ignore
    post_run_analysis_list: ClassVar = [
        FilterBy(
            filters={
                "bb_advice": [("IN", "sell|buy")],
                "rsi_advice": [("IN", "sell|buy")],
                "ma_trend_short": [("IN", "buy")],
                "Stock_Index": [("IN", "FTSE_100|FTSE_250")],
            }
        ),
        SortBy(
            columns=[
                "Date",
                "bb_advice",
                "rsi_advice",
                "ma_trend_short",
                "bb_diff_percent",
                "rsi",
                "Ticker",
            ],
            orders_asc=[
                True,
                False,
                False,
                False,
                True,
                True,
                True,
            ],
        ),
    ]  # type: ignore
    columns_to_plot: ClassVar = [*technical_indicators, "Close"]  # type: ignore

    def _set_main_advice_column(self: Self, data: pd.DataFrame) -> pd.DataFrame:
        """Set main_advice data frame."""
        data["main_advice"] = "neutral"

        data.loc[
            (data["bb_advice"] == "buy")
            & (data["rsi_advice"] == "buy")
            & (data["ma_trend_short"] == "buy"),
            "main_advice",
        ] = "buy"

        data.loc[
            (data["bb_advice"] == "sell") | (data["rsi_advice"] == "sell"),
            # OR 7% stop / loss rule
            "main_advice",
        ] = "sell"

        return data
