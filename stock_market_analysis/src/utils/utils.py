"""Helper functions."""

import pickle
from functools import wraps
from hashlib import sha256
from pathlib import Path
from typing import Any, Callable

import pandas as pd
import yfinance as yf
from tabulate import tabulate

from stock_market_analysis.src.logger import logger


EMPTY_DF = pd.DataFrame([])


def log_dataframe_pretty(df: pd.DataFrame):
    """Pretty print pandas dataframe using tabulate."""
    table_string = tabulate(
        df, headers="keys", tablefmt="psql"
    )  # Convert DataFrame to pretty table
    logger.info(f"\n{table_string}")


def s3_save_pd_dataframe(df: pd.DataFrame, bucket: str, key: str):
    """Save pandas dataframe to s3 as parquet file."""
    # Convert DataFrame to Parquet
    s3_path = f"s3://{bucket}/{key}"
    if df is None or df.empty:
        logger.warning(f"Skipping saving empty df into: {s3_path}")
        return
    logger.info(f"Saving pd.DataFrame into: {s3_path}")
    # df.to_parquet(s3_path, engine="fastparquet", compression="snappy")
    df.to_csv(s3_path, index=False)


def cache_to_pickle(cache_dir: Path) -> Callable:
    """Cache the output of a function to a pickle file based on input parameters.

    Args:
    ----
        cache_dir (str): Directory where cache files will be stored.

    Returns:
    -------
        Callable: Decorated function with caching enabled.
    """
    cache_dir.mkdir(parents=True, exist_ok=True)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: list[any], **kwargs: dict[str, any]) -> any:  # type: ignore
            # Create a unique cache key based on the function name and arguments
            cache_key = sha256(
                (func.__name__ + str(args) + str(kwargs)).encode()
            ).hexdigest()
            cache_file = cache_dir / f"{cache_key}.pkl"

            # If cache file exists, load and return the cached result
            if cache_file.exists():
                with cache_file.open("rb") as f:
                    logger.debug(f"Loading cached result from {cache_file}")
                    return pickle.load(f)  # noqa: S301

            # Call the function and cache the result
            result = func(*args, **kwargs)
            if isinstance(result, pd.DataFrame):
                with cache_file.open("wb") as f:
                    logger.debug(f"Caching result to {cache_file}")
                    pickle.dump(result, f)

            return result

        return wrapper

    return decorator


@cache_to_pickle(Path("/tmp/cache/yf_download"))  # noqa: S108
def yf_download(*args: Any, **kwargs: Any):  # noqa: ANN401
    """Download data from yahoo finance and store as pickled data."""
    logger.info(
        "Downloading Yahoo Finance data for: args=(%s); kwargs=(%s)", args, kwargs
    )
    return yf.download(*args, **kwargs)


def parse_sort_input(input_string: str | None) -> tuple[list[str], list[bool]]:
    """Parse sort input into lists of columns and orders."""
    if not input_string:
        return [], []

    column_specs = input_string.split(",")

    columns = []
    order_asc_column = []

    for spec_orig in column_specs:
        spec = spec_orig.strip()  # Remove any leading/trailing whitespace

        if "[desc]" in spec:
            columns.append(spec.replace("[desc]", ""))
            order_asc_column.append(False)
        elif "[asc]" in spec:
            columns.append(spec.replace("[asc]", ""))
            order_asc_column.append(True)
        else:
            columns.append(spec)
            order_asc_column.append(True)  # Default to ascending if not specified

    return columns, order_asc_column


def parse_filters_input(input_string: str | None) -> dict:
    """Parse input filters string into dict of filters."""
    # Split the string into key-value pairs
    if not input_string:
        return {}

    pairs = input_string.split(",")
    result = {}  # type: ignore
    for pair in pairs:
        key, value = pair.split("=")
        if key not in result:
            result[key] = []
        if value.startswith("NON_"):
            result[key].append(("NON_", value))
        else:
            result[key].append(("IN", value))
    return result


def check_columns_exist_in_df(df: pd.DataFrame, required_columns: list) -> None:
    """Check if all required columns exist in the DataFrame.

    Args:
    ----
    df (pd.DataFrame): The DataFrame to check.
    required_columns (list): List of column names to check for.

    Raises:
    ------
    ValueError: If any of the required columns are missing from the DataFrame.
    """
    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        missing_cols_str = ", ".join(missing_columns)
        msg = f"The following required columns are missing from the DataFrame: {missing_cols_str}"
        raise ValueError(msg)
