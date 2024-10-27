from stock_market_analysis.src.data_providers.yahoo_data import YahooDataProvider
from stock_market_analysis.src.services.rsi_service import RSIBaseService


def test_analyze_single_ticker_contains_close_price_and_ticker():
    analysis_service = RSIBaseService()
    data = analysis_service.run("AAPL", "1y")
    assert "Close" in data
    assert "Ticker" in data


def test_yahoo_data_provider_contains_close_price():
    data_provider = YahooDataProvider()
    data = data_provider.get_data("AAPL", "1y")
    assert "Close" in data
