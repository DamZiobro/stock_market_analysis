"""Interface for command line tool."""

import importlib

import click


@click.group()
def tech_analysis():
    """CLI command group."""


@tech_analysis.command()
def version():
    """Return version of this tool."""
    click.echo(importlib.metadata.version("stock_market_analysis"))
