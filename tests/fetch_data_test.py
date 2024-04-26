from pydantic import FilePath

from stock_market_analysis.steps.fetchData import CSVData, read_csv


def test_read_csv():
    test_path = FilePath("stock_market_analysis/data/ftse.csv")
    data = read_csv(test_path)
    assert len(data) > 0, "Should return non-empty list"
    assert all(
        isinstance(item, CSVData) for item in data
    ), "All items should be instances of CSVData"
