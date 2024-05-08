"""Interface for command line tool."""

import importlib.metadata
from datetime import datetime
from typing import List

import click
from pydantic import BaseModel

from stock_market_analysis.src.stock_data_fetcher import (
    fetch_close_price,
    fetch_close_prices,
    fetch_historic_dividends,
)


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
@click.argument("stock_symbol", type=str)
@click.option(
    "--days",
    default=15,
    show_default=True,
    help="Number of days to fetch historical close prices for",
    type=int,
)
def close_prices(stock_symbol: str, days: int = 15):
    """Fetch historical close prices for a given stock symbol over a specified number of days.

    Args:
    ----
        stock_symbol (str): The stock ticker symbol for which historical data is fetched.
        days (Optional[int]): The number of days to fetch historical prices for. Defaults to 15.

    Returns:
    -------
        Prints the fetched historical prices.

    Raises:
    ------
        Prints an error message if data fetching fails.
    """
    prices = fetch_close_prices(stock_symbol, days=days)
    data_response = HistoricalDataResponse(prices=prices)
    click.echo(f"Historical Prices for {stock_symbol}: {data_response.prices}")


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


@click.group()
def cli():
    """CLI main command group."""


cli.add_command(general)
cli.add_command(stock_data)
