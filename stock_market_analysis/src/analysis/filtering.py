from typing import Optional, TypeVar

import pandas as pd

from stock_market_analysis.src.analysis.base_analysis import BaseAnalysis
from stock_market_analysis.src.logger import logger


Self = TypeVar("Self", bound="FilterBy")


class FilterBy(BaseAnalysis):
    """Sorting input data by date (which is index)."""

    def __init__(self: Self, filters: Optional[dict] = None) -> None:
        """Sort provided columns by provided orders."""
        if filters is None:
            filters = {}
        self.filters = filters
        logger.info(
            "Preparing filtering by filters: '%s'",
            str(self.filters),
        )

    def apply(self: Self, df: pd.DataFrame):
        """Apply analysis to the data from data_df."""
        mask = pd.Series(True, index=df.index)
        for column, conditions in self.filters.items():
            if column in df.columns:
                column_mask = pd.Series(False, index=df.index)

                # for single values of filtering
                if not isinstance(conditions, list):
                    conditions = [("IN", conditions)]  # noqa: PLW2901

                for op, value in conditions:
                    if column == "Date":
                        df[column] = pd.to_datetime(df[column])
                        value = pd.to_datetime(value)  # noqa: PLW2901
                    if op == "NON_":
                        column_mask |= ~df[column].isin(
                            value.replace("NON_", "").split("|")
                        )
                    else:  # 'IN' operator
                        column_mask |= df[column].isin(
                            value.split("|") if isinstance(value, str) else [value]
                        )
                mask &= column_mask

        return df[mask]
