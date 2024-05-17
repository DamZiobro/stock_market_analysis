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


def s3_save_pd_dataframe(df: pd.DataFrame, bucket: str, key: str):
    """Save pandas dataframe to s3 as parquet file."""
    # Convert DataFrame to Parquet
    s3_path = f"s3://{bucket}/{key}"
    if df is None or df.empty:
        logger.warning(f"Skipping saving empty df into: {s3_path}")
        return
    logger.info(f"Saving pd.DataFrame into: {s3_path}")
    #df.to_parquet(s3_path, engine="fastparquet", compression="snappy")
    df.to_csv(s3_path, index=False)
