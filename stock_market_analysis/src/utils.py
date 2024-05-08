"""Helper functions."""

import pandas as pd
from tabulate import tabulate

from stock_market_analysis.src.logger import logger


def log_dataframe_pretty(df: pd.DataFrame):
    """Pretty print pandas dataframe using tabulate."""
    table_string = tabulate(
        df, headers="keys", tablefmt="psql"
    )  # Convert DataFrame to pretty table
    logger.info(table_string)
