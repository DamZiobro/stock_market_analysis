from typing import ClassVar

from stock_market_analysis.src.analysis.filtering import FilterBy
from stock_market_analysis.src.analysis.sorting import SortBy
from stock_market_analysis.src.data_providers.yahoo_data import YahooDataProvider
from stock_market_analysis.src.services.base_service import BaseAnalysisService
from stock_market_analysis.src.strategies.bb import BBOverupperUnderlowerStrategy


class BBBaseService(BaseAnalysisService):
    """Facade service for stock market analysis."""

    data_provider: ClassVar = YahooDataProvider()  # type: ignore
    technical_indicators: ClassVar = ["bb_upper", "bb_lower"]  # type: ignore
    pre_run_strategies: ClassVar = [BBOverupperUnderlowerStrategy()]  # type: ignore
    post_run_analysis_list: ClassVar = [
        FilterBy(filters={"bb_meaning": [("IN", "overupper|underlower")]}),
        SortBy(
            columns=["Date", "bb_advice", "bb_diff_percent"],
            orders_asc=[True, True, True],
        ),
    ]  # type: ignore
    backtest_main_advice_column: ClassVar = "bb_advice"  # type: ignore
    columns_to_plot: ClassVar = [*technical_indicators, "Close"]  # type: ignore
