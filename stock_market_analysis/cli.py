"""Interface for command line tool."""

import importlib.metadata

import click


@click.group()
def cli():
    """CLI command group."""


@cli.command()
def hello_world():
    """Hello world."""
    click.echo("hello world")


@cli.command()
def version():
    """Return version of this tool."""
    click.echo(importlib.metadata.version("stock_market_analysis"))
