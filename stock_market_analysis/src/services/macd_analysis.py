from typing import ClassVar

from stock_market_analysis.src.data_providers.yahoo_data import YahooDataProvider
from stock_market_analysis.src.services.base_service import BaseAnalysisService
from stock_market_analysis.src.strategies.macd import MACDDay3BuyDay3SellStrategy


class MACDAnalysisService(BaseAnalysisService):
    """Facade service for stock market analysis."""

    data_provider: ClassVar = YahooDataProvider()  # type: ignore
    strategies: ClassVar = [MACDDay3BuyDay3SellStrategy()]  # type: ignore
    technical_indicators: ClassVar = ["macd"]
    columns_to_plot: ClassVar = [*technical_indicators, "Close"]  # type: ignore
