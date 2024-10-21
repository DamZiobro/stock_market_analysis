from typing import TYPE_CHECKING, Optional, TypeVar

import pandas as pd

from stock_market_analysis.src.indicators.technical_indicators import (
    TechnicalIndicators,
)
from stock_market_analysis.src.output.csv_output import CSVOutput
from stock_market_analysis.src.output.plot_output import PlotOutput


if TYPE_CHECKING:
    from stock_market_analysis.src.output.base_output import BaseOutput


Self = TypeVar("Self", bound="BaseAnalysisService")


class BaseAnalysisService:
    """Facade service for stock market analysis."""

    indicator_service = TechnicalIndicators()
    data_provider = None  # must be overwritten in concrete classes
    strategies = None  # must be overwritten in concrete classes
    selected_indicators = None  # could be overwritten in concrete classes
    columns_to_plot = None  # must be overwritten in concrete classes

    def analyze(self: Self, ticker: str, period: str) -> None:
        """Analyze a single stock ticker.

        Args:
        ----
            ticker (str): Stock ticker symbol
            output_format (str): Output format ('csv', 'json', 'plot')
            period (str): Data period (e.g., '1y', '2023-01-01:2024-01-01')
        """
        # Fetch and prepare data
        data_df = self.data_provider.get_data(ticker, period)  # type: ignore
        if data_df.empty:
            return data_df

        data_df["Ticker"] = ticker

        # Apply technical indicators
        data_df = self.indicator_service.add_indicators(
            data_df, self.selected_indicators  # type: ignore
        )

        # Apply strategies
        for strategy in self.strategies: # type: ignore
            strategy.apply(data_df)  # type: ignore

        return data_df

    def output_data(
        self: Self,
        data_df: pd.DataFrame,
        output_format: str,
        output_file: Optional[str] = None,
    ) -> None:
        """Save data to one of the formats."""
        # Output data
        output: BaseOutput | None = None
        if output_format == "csv":
            output = CSVOutput()
            output.render(data_df, output_file)
        elif output_format == "plot":
            output = PlotOutput()
            output.render(data_df, output_file, self.columns_to_plot)
        else:
            msg = "Unsupported output format."
            raise ValueError(msg)
