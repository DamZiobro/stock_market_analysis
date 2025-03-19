from typing import ClassVar

from stock_market_analysis.src.analysis.filtering import FilterBy
from stock_market_analysis.src.analysis.sorting import SortBy
from stock_market_analysis.src.data_providers.yahoo_data import YahooDataProvider
from stock_market_analysis.src.services.base_service import BaseAnalysisService
from stock_market_analysis.src.strategies.ten_days import TenDaysLowsHighsStrategy


class TenDaysLowsHighsService(BaseAnalysisService):
    """Facade service for stock market analysis."""

    data_provider: ClassVar = YahooDataProvider()  # type: ignore
    technical_indicators: ClassVar = []  # type: ignore
    pre_run_strategies: ClassVar = [TenDaysLowsHighsStrategy()]  # type: ignore
    post_run_analysis_list: ClassVar = [
        FilterBy(
            filters={
                "ten_days_advice": [("IN", "buy|sell")],
                "Stock_Index": [("IN", "FTSE_100|FTSE_250")],
            }
        ),
        SortBy(
            columns=[
                "Date",
                "ten_days_advice",
                "ten_days_score",
                "Stock_Index",
                "Ticker",
            ],
            orders_asc=[
                True,
                True,
                False,
                True,
                True,
            ],
        ),
    ]  # type: ignore
    backtest_main_advice_column: ClassVar = "ten_days_advice"  # type: ignore
    columns_to_plot: ClassVar = [*technical_indicators, "Close"]  # type: ignore
