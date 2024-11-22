from typing import ClassVar, TypeVar

import pandas as pd

from stock_market_analysis.src.analysis.filtering import FilterBy
from stock_market_analysis.src.analysis.sorting import SortBy
from stock_market_analysis.src.data_providers.yahoo_data import YahooDataProvider
from stock_market_analysis.src.services.base_service import BaseAnalysisService
from stock_market_analysis.src.strategies.four_ps import (
    Phases4PSDetectionStrategy,
)


Self = TypeVar("Self", bound="FourPSService")


class FourPSService(BaseAnalysisService):
    """Facade service for stock market analysis.

    Backtested 1 year from 27.10.2024 this strategy gave 10% gain
    """

    data_provider: ClassVar = YahooDataProvider()  # type: ignore
    technical_indicators: ClassVar = [
        "ma_50",
        "ma_200",
        "ma_50_slope",
        "ma_200_slope",
        "bb_upper",
        "bb_lower",
        "momentum_10",
        "macd",
        "macd_signal",
        "rsi",
    ]
    pre_run_strategies: ClassVar = [
        Phases4PSDetectionStrategy(),
        # apply only for sideways markets
        # add another exit strategy (ex. 3 days macd declining) - see Burberry
        # include moving averages?
    ]  # type: ignore
    post_run_analysis_list: ClassVar = [
        FilterBy(
            filters={
                #"4ps_phase": [("IN", "new_trend")],
                # "4ps_advice": [("IN", "sell|buy")],
                "Stock_Index": [("IN", "FTSE_100|FTSE_250")],
            }
        ),
        SortBy(
            columns=[
                "Ticker",
                "Date",
                "4ps_advice",
            ],
            orders_asc=[
                True,
                True,
                False,
            ],
        ),
    ]  # type: ignore
    columns_to_plot: ClassVar = [*technical_indicators, "Close"]  # type: ignore

    def _set_main_advice_column(self: Self, data: pd.DataFrame) -> pd.DataFrame:
        """Set main_advice data frame."""
        data["main_advice"] = data["4ps_advice"]
        return data
