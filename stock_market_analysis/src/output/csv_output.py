from typing import Optional, TypeVar

import pandas as pd

from stock_market_analysis.src.logger import logger
from stock_market_analysis.src.output.base_output import BaseOutput
from stock_market_analysis.src.utils.utils import log_dataframe_pretty


Self = TypeVar("Self", bound="CSVOutput")


class CSVOutput(BaseOutput):
    """Outputs data in CSV format."""

    def render(self: Self, df: pd.DataFrame, filename: Optional[str] = None) -> None:
        """Save DataFrame to CSV."""
        if filename is None:
            log_dataframe_pretty(df)
        else:
            logger.info("Saving data into CSV file: %s", filename)
            df.to_csv(filename)
