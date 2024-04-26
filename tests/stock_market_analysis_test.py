"""Unit tests of stock-market-analysis."""

import pytest
from click.testing import CliRunner

from stock_market_analysis.cli import (
    hello_world,
    version,
)


@pytest.fixture()
def cli_runner():
    return CliRunner()

def test_version(cli_runner: CliRunner):
    """Verify version."""
    result = cli_runner.invoke(version)
    assert result.exit_code == 0
    assert result.output.strip() == "0.0.1"


def test_stock_market_analysis_returns_hello_world(cli_runner: CliRunner):
    """Verify output of fetch function."""
    result = cli_runner.invoke(hello_world)
    assert result.exit_code == 0
    assert result.output.strip() == "hello world"

