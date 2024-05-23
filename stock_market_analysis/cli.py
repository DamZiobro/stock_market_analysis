"""Interface for command line tool."""

import importlib.metadata
from datetime import datetime
from typing import List

import click
import pandas as pd
from pydantic import BaseModel

from stock_market_analysis.src.stock_data_fetcher import (
    fetch_chart_trend,
    fetch_chart_trends,
    fetch_close_price,
    fetch_close_prices,
    fetch_historic_dividends,
    fetch_volume_analysis_data,
    fetch_volume_analysis_data_multiple_tickers,
)
from stock_market_analysis.src.utils import log_dataframe_pretty
from stock_market_analysis.steps.dividendCaptureAnalysis import (
    get_dividend_capture_return,
)


PATH_TO_FTSE_CSV = "stock_market_analysis/data/ftse.csv"


class HistoricalDataResponse(BaseModel):
    """Response of historical data."""

    prices: List[float]


@click.group()
def general():
    """CLI command group."""


@click.group()
def stock_data():
    """CLI command group."""


@general.command()
def version():
    """Return version of this tool."""
    click.echo(importlib.metadata.version("stock_market_analysis"))


@stock_data.command()
@click.option("--ticker", help="Stock ticker symbol, e.g., AAPL")
@click.option(
    "--days",
    default=15,
    show_default=True,
    help="Number of days to fetch historical close prices for",
    type=int,
)
def close_prices(ticker: str, days: int = 15):
    """Fetch historical close prices for a given stock symbol over a specified number of days.

    Args:
    ----
        ticker (str): The stock ticker symbol for which historical data is fetched.
        days (Optional[int]): The number of days to fetch historical prices for. Defaults to 15.

    Returns:
    -------
        Prints the fetched historical prices.

    Raises:
    ------
        Prints an error message if data fetching fails.
    """
    prices = fetch_close_prices(ticker, days=days)
    data_response = HistoricalDataResponse(prices=prices)
    click.echo(f"Historical Prices for {ticker}: {data_response.prices}")


@stock_data.command()
@click.option("--ticker", help="Stock ticker symbol, e.g., AAPL")
@click.option(
    "--date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="Date for fetching the close price (format: YYYY-MM-DD)",
)
def close_price(ticker: str, date: datetime):
    """Command-line tool to fetch the closing price of a stock on a specified date."""
    try:
        price = fetch_close_price(ticker, date)
        if price is not None:
            click.echo(
                f"The closing price for {ticker} on {date.date()} was ${price:.2f}"
            )
        else:
            click.echo("No data available for the specified date.")
    except ValueError as e:
        click.echo(f"Error: {e}")


@stock_data.command()
@click.option("--ticker", type=str, help="The stock ticker symbol (e.g., 'AAPL').")
@click.option(
    "--limit",
    default=10,
    show_default=True,
    help="Number of days to fetch historical data for",
    type=int,
)
def historic_dividends(ticker: str, limit: int = 10):
    """Command-line tool to fetch the historical dividends of a stock."""
    dividends = fetch_historic_dividends(ticker, limit)
    if dividends is not None:
        click.echo(f"Dividends for {ticker}:\n{dividends}")
    else:
        click.echo(f"No dividend data available for {ticker}.")


@stock_data.command()
@click.option("--ticker", type=str, required=True, help="Stock ticker symbol")
@click.option(
    "--investment_amount", type=int, default=10000, help="Amount in GBP to be invested"
)
@click.option(
    "--limit", type=int, default=10, help="Number of recent dividends to analyze"
)
@click.option(
    "--transactions_fees",
    type=float,
    default=0.00,
    help="Transaction fees for buying and selling",
)
def dividend_capture_analysis(
    ticker: str, investment_amount: int, limit: int, transactions_fees: float
):
    """Command-line tool to calculate the investment return for buying stock before ex-div date.

       and selling on the ex-dividend date.

    Args:
    ----
        ticker (str): The stock ticker symbol.
        investment_amount (int): The amount of money in GBP to invest.
        limit (int): The maximum number of dividend records to process.
        transactions_fees (float): The total transaction fees for buying and selling the stock.

    This tool fetches the dividend history for the given stock ticker and calculates the potential
    returns from investing a specified amount, considering transaction fees.
    """
    returns_df = get_dividend_capture_return(
        ticker=ticker,
        investment_amount=investment_amount,
        limit=limit,
        transactions_fees=transactions_fees,
    )

    if returns_df is not None:
        log_dataframe_pretty(returns_df)


@stock_data.command()
@click.option("--ticker", default="AAPL", help="Stock ticker symbol (e.g., AAPL).")
@click.option(
    "--days", default=90, help="Number of days to consider for the trend analysis."
)
def chart_trend(ticker: str, days: int = 90):
    """Command-line tool to fetch the stock chart trend and it's length in days."""
    stock_trend_info_df = fetch_chart_trend(ticker, days)
    log_dataframe_pretty(stock_trend_info_df)


@stock_data.command()
@click.option(
    "--file",
    type=click.Path(exists=True),
    help="Path to the CSV file containing stock tickers.",
    default=PATH_TO_FTSE_CSV,
)
@click.option(
    "--days",
    default=90,
    help="Number of days to consider for the trend analysis.",
    type=int,
)
@click.option(
    "--window",
    default=30,
    help="Window size for calculating the moving average.",
    type=int,
)
def chart_trends(
    file: click.Path = PATH_TO_FTSE_CSV,  # type: ignore
    days: int = 90,
    window: int = 30,
):
    """Read stock codes from a CSV file and fetches their trend information."""
    # Read tickers from the CSV file
    tickers_df = pd.read_csv(file)
    tickers = tickers_df["Code"].tolist()

    # Call the function to get trends
    trends = fetch_chart_trends(tickers, days, window)

    # Print the resulting DataFrame
    pd.set_option("display.max_rows", None)
    if not trends.empty:
        log_dataframe_pretty(trends)
    else:
        click.echo("No trend data available.")


@stock_data.command()
@click.option("--ticker", default="AAPL", help="Stock ticker symbol (e.g., AAPL).")
@click.option(
    "--days", default=90, help="Number of days to consider for the trend analysis."
)
def volume_analysis_single(ticker: str, days: int = 90):
    """Command-line tool to fetch the stock chart trend and it's length in days."""
    volume_analysis_df = fetch_volume_analysis_data(ticker, days)
    log_dataframe_pretty(volume_analysis_df)


@stock_data.command()
@click.option(
    "--file",
    type=click.Path(exists=True),
    help="Path to the CSV file containing stock tickers.",
    default=PATH_TO_FTSE_CSV,
)
@click.option(
    "--days",
    default=90,
    help="Number of days to consider for the trend analysis.",
    type=int,
)
@click.option(
    "--window",
    default=30,
    help="Window size for calculating the moving average.",
    type=int,
)
def volume_analysis(
    file: click.Path = PATH_TO_FTSE_CSV,  # type: ignore
    days: int = 90,
    window: int = 30,
):
    """Read stock codes from a CSV file and fetches their trend information."""
    # Read tickers from the CSV file
    tickers_df = pd.read_csv(file)
    tickers = tickers_df["Code"].tolist()

    # Call the function to get trends
    volumes = fetch_volume_analysis_data_multiple_tickers(tickers, days)
    trends = fetch_chart_trends(tickers, days, window)

    result_df = trends.merge(volumes, on="Company code")
    result_df = result_df.sort_values(
        by=[
            "Trend Direction",
            "Trend Duration (days)",
            "increasing_volume_days",
            "average_volume",
            "decreasing_volume_days",
        ],
        ascending=[False, False, False, False, False],
    )
    result_df = result_df.reset_index(drop=True)

    # Print the resulting DataFrame
    pd.set_option("display.max_rows", None)
    if not volumes.empty:
        log_dataframe_pretty(result_df)
    else:
        click.echo("No trend data available.")


@click.group()
def cli():
    """CLI main command group."""


cli.add_command(general)
cli.add_command(stock_data)
