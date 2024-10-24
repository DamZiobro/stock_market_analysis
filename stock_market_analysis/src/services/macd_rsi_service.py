from typing import ClassVar, TypeVar

from stock_market_analysis.src.analysis.filtering import FilterBy
from stock_market_analysis.src.analysis.sorting import SortBy
from stock_market_analysis.src.data_providers.yahoo_data import YahooDataProvider
from stock_market_analysis.src.services.base_service import BaseAnalysisService
from stock_market_analysis.src.strategies.macd import MACDDay3BuyDay3SellStrategy
from stock_market_analysis.src.strategies.rsi import RSIOverboughtOversoldStrategy


Self = TypeVar("Self", bound="MACD3DaysRSIService")


class MACD3DaysRSIService(BaseAnalysisService):
    """Facade service for stock market analysis."""

    data_provider: ClassVar = YahooDataProvider()  # type: ignore
    technical_indicators: ClassVar = ["rsi", "macd"]
    pre_run_strategies: ClassVar = [
        RSIOverboughtOversoldStrategy(),
        MACDDay3BuyDay3SellStrategy(),
    ]  # type: ignore
    post_run_analysis_list: ClassVar = [
        FilterBy(filters={"macd_advice": [("IN", "sell|buy")]}),
        SortBy(
            columns=["Date", "macd_advice", "rsi_category", "macd_hist_diff", "Ticker"],
            orders_asc=[True, False, False, True, True],
        ),
    ]  # type: ignore
    backtest_main_advice_column: ClassVar = "macd_advice"  # type: ignore
    columns_to_plot: ClassVar = [*technical_indicators, "Close"]  # type: ignore
