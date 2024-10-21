"""Interface for command line tool."""

import importlib

import click
import pandas as pd
from joblib import Parallel, delayed

from stock_market_analysis.src.services.rsi_analysis import RSIAnalysisService


PATH_TO_FTSE_CSV = "stock_market_analysis/data/ftse.csv"


@click.group()
def tech_analysis():
    """CLI command group."""


@tech_analysis.command()
def version():
    """Return version of this tool."""
    click.echo(importlib.metadata.version("stock_market_analysis"))


@tech_analysis.command()
@click.option("--ticker", help="Stock ticker symbol to analyze.", default=None)
@click.option(
    "--file",
    help=f"File containing list of tickers to analyze. Defaults to: {PATH_TO_FTSE_CSV}",
    default=PATH_TO_FTSE_CSV,
)
@click.option(
    "--period",
    default="1y",
    help="Data period (e.g., '1y', '6mo', or '2023-01-01:2024-01-01')",
)
@click.option("--output", default="csv", help="Output format: csv, json, plot")
@click.option("--save", default=False, help="Save output to file?")
def analyze(ticker: str, file: click.Path, period: str, output: str, save: bool):
    """CLI command to analyze stock based on ticker, output format, and period."""
    if ticker is not None:
        tickers = [ticker]
    else:
        tickers_df = pd.read_csv(file)
        tickers = tickers_df["Code"].tolist()

    analysis = RSIAnalysisService()

    results = Parallel(n_jobs=-1)(
        delayed(analysis.analyze)(ticker, period) for ticker in tickers
    )
    result_df = pd.concat(results)

    output_file = None
    if save:
        extension = "png" if output == "plot" else output
        output_file = f"{ticker}_rsi_analysis.{extension}"
    analysis.output_data(result_df, output, output_file)
