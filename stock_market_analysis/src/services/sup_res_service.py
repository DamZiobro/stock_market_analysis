from typing import ClassVar

from stock_market_analysis.src.analysis.filtering import FilterBy
from stock_market_analysis.src.analysis.sorting import SortBy
from stock_market_analysis.src.data_providers.yahoo_data import YahooDataProvider
from stock_market_analysis.src.services.base_service import BaseAnalysisService
from stock_market_analysis.src.strategies.sup_res import SupportResistanceStrategy


class SupportResistanceService(BaseAnalysisService):
    """Facade service for stock market analysis."""

    data_provider: ClassVar = YahooDataProvider()  # type: ignore
    technical_indicators: ClassVar = []  # type: ignore
    pre_run_strategies: ClassVar = [SupportResistanceStrategy()]  # type: ignore
    post_run_analysis_list: ClassVar = [
        FilterBy(
            filters={
                "sup_res_advice": [("IN", "buy|sell")],
                "Stock_Index": [("IN", "FTSE_100|FTSE_250")],
            }
        ),
        SortBy(
            columns=[
                "Date",
                "sup_res_advice",
                "sup_res_window",
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
    backtest_main_advice_column: ClassVar = "sup_res_advice"  # type: ignore
    columns_to_plot: ClassVar = [*technical_indicators, "Close"]  # type: ignore
