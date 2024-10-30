from typing import ClassVar, TypeVar

from stock_market_analysis.src.analysis.filtering import FilterBy
from stock_market_analysis.src.analysis.sorting import SortBy
from stock_market_analysis.src.data_providers.yahoo_data import YahooDataProvider
from stock_market_analysis.src.services.base_service import BaseAnalysisService
from stock_market_analysis.src.strategies.ma import (
    MovingAverageGetTrandDirectionStrategy,
    MovingAverageTrendBasedStrategy,
)
from stock_market_analysis.src.strategies.macd import MACDTrendBasedAdviceStrategy
from stock_market_analysis.src.strategies.main import MainAdviceScoreStrategy
from stock_market_analysis.src.strategies.rsi import RSITrendBasedStrategy


Self = TypeVar("Self", bound="TrendBasedService")


class TrendBasedService(BaseAnalysisService):
    """Facade service for stock market analysis.

    Backtested 1 year from 30.10.2024 this strategy gave 20% gain
    """

    data_provider: ClassVar = YahooDataProvider()  # type: ignore
    technical_indicators: ClassVar = [
        "rsi",
        "macd",
        "macd_signal",
        "ma_short",
        "ma_medium",
        "ma_long",
    ]
    pre_run_strategies: ClassVar = [
        MovingAverageGetTrandDirectionStrategy(),
        MACDTrendBasedAdviceStrategy(),
        RSITrendBasedStrategy(),
        MovingAverageTrendBasedStrategy(),
        MainAdviceScoreStrategy(
            buy_score_threshold=0.3,
            score_score_threshold=-0.3,
            advice_weights={
                "rsi_advice": 0.3,
                "macd_advice": 0.4,
                "ma_short_advice": 0.3,
            },
        ),
    ]  # type: ignore
    post_run_analysis_list: ClassVar = [
        FilterBy(
            filters={
                "main_advice": [("IN", "buy|sell")],
                "Stock_Index": [("IN", "FTSE_100|FTSE_250")],
            }
        ),
        SortBy(
            columns=[
                "Date",
                "main_advice",
                "main_advice_score",
                "macd_advice",
                "rsi_advice",
                "ma_short_advice",
                "Stock_Index",
                "Ticker",
            ],
            orders_asc=[
                True,
                True,
                False,
                False,
                False,
                False,
                True,
                True,
            ],
        ),
    ]  # type: ignore
    columns_to_plot: ClassVar = [*technical_indicators, "Close"]  # type: ignore
