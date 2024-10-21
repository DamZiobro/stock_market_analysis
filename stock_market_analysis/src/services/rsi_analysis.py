from typing import ClassVar

from stock_market_analysis.src.data_providers.yahoo_data import YahooDataProvider
from stock_market_analysis.src.services.base_service import BaseAnalysisService
from stock_market_analysis.src.strategies.rsi import RSIOverboughtOversoldStrategy


class RSIAnalysisService(BaseAnalysisService):
    """Facade service for stock market analysis."""

    data_provider: ClassVar = YahooDataProvider()  # type: ignore
    strategies: ClassVar = [RSIOverboughtOversoldStrategy()]  # type: ignore
    technical_indicators: ClassVar = ["rsi"]  # type: ignore
    columns_to_plot: ClassVar = [*technical_indicators, "Close"]  # type: ignore
