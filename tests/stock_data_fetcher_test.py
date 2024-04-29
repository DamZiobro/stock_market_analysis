import unittest
from unittest.mock import Mock, patch

import pandas as pd

from stock_market_analysis.src.stock_data_fetcher import fetch_historical_data


@patch("stock_market_analysis.src.stock_data_fetcher.Ticker")
def test_fetch_historical_data(mock_ticker: Mock):
    # Prepare a DataFrame to mimic yfinance output
    data = {"Close": [100.0, 105.0, 110.0, 115.0, 120.0]}
    df = pd.DataFrame(data)

    # Set the return value of the history method
    mock_ticker.return_value.history.return_value = df

    # Expected number of days
    expected_days = 5
    stock_symbol = "AAPL"

    # Call the function
    result = fetch_historical_data(stock_symbol, days=expected_days)

    # Assertions to validate behavior
    assert isinstance(result, list), "The result should be a list"
    assert (
        len(result) == expected_days
    ), "The list should contain data for the expected number of days"
    assert result == [
        100.0,
        105.0,
        110.0,
        115.0,
        120.0,
    ], "The prices should match the expected values"


if __name__ == "__main__":
    unittest.main()
