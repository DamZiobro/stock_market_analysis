"""Helper functions."""

import inspect
import pickle
from datetime import datetime, timedelta
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
        def wrapper(*args: list[Any], **kwargs: dict) -> any:  # type: ignore
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
    df = yf.download(*args, **kwargs)
    df.columns = df.columns.get_level_values(0)
    return df


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


def get_class_init_params(obj: Any):  # noqa: ANN401
    """Get class name and class init params based on it's object."""
    # Get the __init__ method signature
    signature = inspect.signature(obj.__class__.__init__)

    # Get all attributes of the object
    attributes = {
        name: getattr(obj, name)
        for name in dir(obj)
        if not name.startswith("__") and not callable(getattr(obj, name))
    }

    params = {}
    for name, _param in signature.parameters.items():
        if name == "self":
            continue
        if name == "args":
            if hasattr(obj, "args"):
                params["*args"] = obj.args
        elif name == "kwargs":
            if hasattr(obj, "kwargs"):
                params["**kwargs"] = obj.kwargs
        else:
            params[name] = attributes.get(name, "<not set or not accessible>")

    return obj.__class__.__name__, params


def get_date_range(date_input: str):
    """Get date range from yf.download-like period."""
    if ":" in date_input:
        start_date_str, end_date_str = date_input.split(":")
        return start_date_str, end_date_str  # Already in string format

    end_date = datetime.now()  # noqa: DTZ005
    if date_input.endswith("d"):
        days = int(date_input[:-1])
        start_date = end_date - timedelta(days=days)
    elif date_input.endswith("mo"):
        months = int(date_input[:-2])
        start_date = end_date - pd.DateOffset(months=months)
    elif date_input.endswith("y"):
        years = int(date_input[:-1])
        start_date = end_date - pd.DateOffset(years=years)
    else:
        msg = "Invalid date format"
        raise ValueError(msg)

    # Convert to string format
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")

    return start_date_str, end_date_str


def inject_missing_dates(df: pd.DataFrame, period: str) -> pd.DataFrame:
    """Inject missing dates into dataframe for full backtesting."""
    start_date, end_date = get_date_range(period)
    # Add an index to preserve original order, prioritizing the 'Date' column
    df["OriginalIndex"] = range(len(df))

    # Generate full date range
    full_dates = pd.date_range(start=start_date, end=end_date)

    # Create a DataFrame with all dates in range but no sorting
    missing_dates = pd.DataFrame({"Date": full_dates})

    # Merge with the original DataFrame, keeping the original rows in place
    merged_df = missing_dates.merge(df, on="Date", how="left")

    # Sort by 'OriginalIndex' and drop the helper column
    merged_df = merged_df.sort_values(by=["Date", "OriginalIndex"], na_position="last")
    merged_df = merged_df.drop(columns=["OriginalIndex"])

    return merged_df.reset_index(drop=True)
