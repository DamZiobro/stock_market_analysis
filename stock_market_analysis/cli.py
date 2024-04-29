"""Interface for command line tool."""

import importlib.metadata
from typing import List

import click
from pydantic import BaseModel

from stock_market_analysis.src.stock_data_fetcher import fetch_historical_data


class HistoricalDataResponse(BaseModel):
    """Response of historical data."""

    prices: List[float]


@click.group()
def cli():
    """CLI command group."""


@cli.command()
def hello_world():
    """Hello world."""
    click.echo("hello world")


@cli.command()
@click.argument("stock_symbol", type=str)
@click.option(
    "--days",
    default=15,
    show_default=True,
    help="Number of days to fetch historical data for",
    type=int,
)
def get_historical_data(stock_symbol: str, days: int = 15):
    """Fetch historical data for a given stock symbol over a specified number of days.

    Args:
    ----
        stock_symbol (str): The stock ticker symbol for which historical data is fetched.
        days (Optional[int]): The number of days to fetch historical data for. Defaults to 15.

    Returns:
    -------
        Prints the fetched historical prices.

    Raises:
    ------
        Prints an error message if data fetching fails.
    """
    prices = fetch_historical_data(stock_symbol, days=days)
    data_response = HistoricalDataResponse(prices=prices)
    click.echo(f"Historical Prices for {stock_symbol}: {data_response.prices}")


@cli.command()
def version():
    """Return version of this tool."""
    click.echo(importlib.metadata.version("stock_market_analysis"))
