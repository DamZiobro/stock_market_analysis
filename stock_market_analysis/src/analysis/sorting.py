from typing import TypeVar

import pandas as pd

from stock_market_analysis.src.analysis.base_analysis import BaseAnalysis
from stock_market_analysis.src.logger import logger


Self = TypeVar("Self", bound="SortBy")


class SortBy(BaseAnalysis):
    """Sorting input data by date (which is index)."""

    def __init__(self: Self, columns: list[str], orders_asc: list[bool]) -> None:
        """Sort provided columns by provided orders."""
        self.columns = columns
        self.order_asc_bools = orders_asc
        logger.info(
            "Preparing sorting by columns: '%s' orders: '%s'",
            str(self.columns),
            str(self.order_asc_bools),
        )

    def apply(self: Self, data_df: pd.DataFrame):
        """Apply analysis to the data from data_df."""
        if not self.columns:
            return data_df

        return data_df.sort_values(by=self.columns, ascending=self.order_asc_bools)
