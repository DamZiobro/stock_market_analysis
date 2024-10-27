from typing import ClassVar

from stock_market_analysis.src.data_providers.yahoo_data import YahooDataProvider
from stock_market_analysis.src.services.base_service import BaseAnalysisService
from stock_market_analysis.src.strategies.macd import MACDDay3BuyDay3SellStrategy


class MACDBaseService(BaseAnalysisService):
    """Facade service for stock market analysis."""

    data_provider: ClassVar = YahooDataProvider()  # type: ignore
    technical_indicators: ClassVar = ["macd"]
    pre_run_strategies: ClassVar = [MACDDay3BuyDay3SellStrategy()]  # type: ignore
    post_run_analysis_list: ClassVar = []  # type: ignore
    columns_to_plot: ClassVar = [*technical_indicators, "Close"]  # type: ignore
