"""Interface for command line tool."""

import click

from stock_market_analysis.cli.new_cli import tech_analysis
from stock_market_analysis.cli.old_cli import general, stock_data


@click.group()
def cli():
    """CLI main command group."""


cli.add_command(general)
cli.add_command(stock_data)
cli.add_command(tech_analysis)
