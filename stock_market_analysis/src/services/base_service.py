from typing import TYPE_CHECKING, ClassVar, Optional, TypeVar

import pandas as pd

from stock_market_analysis.src.indicators.technical_indicators import (
    TechnicalIndicators,
)
from stock_market_analysis.src.logger import logger
from stock_market_analysis.src.output.csv_output import CSVOutput
from stock_market_analysis.src.output.plot_output import PlotOutput
from stock_market_analysis.src.utils.utils import get_class_init_params


if TYPE_CHECKING:
    from stock_market_analysis.src.output.base_output import BaseOutput


Self = TypeVar("Self", bound="BaseAnalysisService")


class BaseAnalysisService:
    """Facade service for stock market analysis."""

    indicator_service = TechnicalIndicators()
    data_provider = None  # must be overwritten in concrete classes
    technical_indicators: ClassVar = []  # could be overwritten in concrete classes
    pre_run_strategies: ClassVar = []  # could be overwritten in concrete classes
    post_run_analysis_list: ClassVar = (
        []
    )  # could be overwritten in the concrete classes
    backtest_main_advice_column = None  # could be overwritten in the concrete classes
    columns_to_plot: ClassVar = []  # could be overwritten in concrete classes

    def run(self: Self, ticker: str, period: str) -> None:
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
            data_df, self.technical_indicators  # type: ignore
        )

        # Apply strategies
        for strategy in self.pre_run_strategies:  # type: ignore
            strategy.apply(data_df)  # type: ignore

        return data_df

    def _print_all_analysis_report(self: Self, data_df: pd.DataFrame) -> None:
        """Print final report after each analysis."""
        logger.info("=========================================================")
        logger.info("                    SERVICE REPORT")
        logger.info("=========================================================")
        logger.info("  SERVICE: %s", self.__class__.__name__)
        logger.info("  APPLIED STRATEGIES:")
        for strategy in self.pre_run_strategies:  # type: ignore
            cls_name, init_params = get_class_init_params(strategy)
            logger.info(f"      - {cls_name}({init_params})")
        logger.info("  APPLIED POST_RUN_ANAYSIS:")
        for analysis in self.post_run_analysis_list:  # type: ignore
            cls_name, init_params = get_class_init_params(analysis)
            logger.info(f"      - {cls_name}({init_params})")
        logger.info("  NUMBER OF FILTERED OUT ROWS: %d", len(data_df))
        logger.info(
            "  BACKTEST MAIN_ADVICE COLUMN: %s", self.backtest_main_advice_column
        )
        logger.info("=========================================================")

    def _set_main_advice_column(self: Self, data_df: pd.DataFrame) -> pd.DataFrame:
        """Set 'main_advice' column needed for backtesting.

        Function could be overwritten in concrete service classes.
        """
        return data_df

    def post_run_analysis(self: Self, data_df: pd.DataFrame) -> pd.DataFrame:
        """Trigger for post-run analysis. data_df contains data of all tickers."""
        for analysis in self.post_run_analysis_list:  # type: ignore
            data_df = analysis.apply(data_df)  # type: ignore

        # set 'main_advice' column for backtesting
        if self.backtest_main_advice_column:
            data_df["main_advice"] = data_df[self.backtest_main_advice_column]
        else:
            self._set_main_advice_column(data_df)

        self._print_all_analysis_report(data_df)
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
