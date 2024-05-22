"""Get top performers of companies."""

import json

import pandas as pd

from stock_market_analysis.src.logger import logger
from stock_market_analysis.src.stock_data_fetcher import fetch_historic_dividends
from stock_market_analysis.src.utils import log_dataframe_pretty, s3_save_pd_dataframe


HL_BUY_AND_SELL_COST = 2 * 11.95  # buy and sell fee in Heargraves and Landsdown


def calculate_dividend_capture_returns(
    df: pd.DataFrame, investment_amount: int = 10000, transactions_fees: float = 0.00
) -> pd.DataFrame:
    """Process a DataFrame that includes dividend data and share prices to calculate returns.

    Args:
    ----
        df (DataFrame): A DataFrame containing 'Day Before Price' and 'Ex-Date Price' columns.
        investment_amount(int): investment amount in GBP
        transactions_fees(float): fees related to transactons (buying and selling)

    Returns:
    -------
        DataFrame: The updated DataFrame with new columns for profit in GBP and percent profit.

    Calculates:
    1) The profit in GBP from investing £10,000 buying shares the day before the ex-dividend date
       and selling them the day after.
    2) The percentage of the profit from the investment.
    """
    # Ensure the DataFrame has the necessary columns
    if "Day Before Price" not in df.columns or "Ex-Date Price" not in df.columns:
        msg = "DataFrame must include 'Day Before Price' and 'Ex-Date Price' columns."
        raise ValueError(msg)

    df["Shares Bought"] = (investment_amount / df["Day Before Price"]).apply(int)
    df["Buying Amount"] = df["Shares Bought"] * df["Day Before Price"]
    df["Selling Amount"] = df["Shares Bought"] * df["Ex-Date Price"]
    df["Dividend Received"] = df["Shares Bought"] * df["Dividend"]
    df["Profit in GBP"] = (
        df["Selling Amount"]
        - df["Buying Amount"]
        + df["Dividend Received"]
        - transactions_fees
    )
    df["Percent Profit"] = (df["Profit in GBP"] / df["Buying Amount"]) * 100
    return df


def get_dividend_capture_return(
    ticker: str,
    investment_amount: int = 10000,
    limit: int = 10,
    transactions_fees: float = HL_BUY_AND_SELL_COST,
):
    """Calculate the return on investment for buying shares a day before the ex-dividend date.

       and selling them on the ex-dividend date for a given stock ticker,
       taking into account transaction fees.

    Args:
    ----
        ticker (str): The stock symbol for which to calculate the dividend day investment returns.
        investment_amount (int): The amount in GBP to be invested in buying the stock.
                                 Default is 10,000 GBP.
        limit (int): The maximum number of recent dividends to consider for the investment
                     calculations. Default is 10.
        transactions_fees (float): The total transaction fees for buying and selling the shares.
                     Default is set to HL_BUY_AND_SELL_COST which must be predefined elsewhere.

    Returns:
    -------
        pandas.DataFrame or None: Returns a DataFrame containing the calculated investment returns
                                  for each dividend-paying date considered under the limit.
                                  Returns None if the company has no dividend history or the
                                  DataFrame cannot be generated.

    Raises:
    ------
        Specific exceptions can be detailed here if there are any that could be specifically
        expected, especially if they relate to external API calls, data fetching, and handling.

    This function fetches historical dividend data, calculates potential investment returns based on
    specified investment strategies, logs results using an information level logging, and finally
    returns the resulting DataFrame. The log includes pretty printing of the DataFrame for
    better readability in logs.
    """
    logger.info("Getting dividend day investment returns for company: '%s'", ticker)
    dividends_df = fetch_historic_dividends(ticker, limit=limit)
    if dividends_df is None:
        logger.info(f"Company '({ticker})' doesn't have dividend history.")
        return None

    return calculate_dividend_capture_returns(
        dividends_df, investment_amount, transactions_fees=transactions_fees
    )


def handler(event: list[dict[str, str]], context: dict):  # noqa: ARG001
    """Handle lambda requestes."""
    logger.info(
        "Analysis of historical dividend profit based on pre-ex-dividend-date purchase."
    )
    logger.info("event: %s", json.dumps(event))

    s3_bucket = "xmementoit-stock-market-analysis-asdfyuxc"
    for item in event:
        ticker = item["Code"]
        s3_key = f"data/dividend_capture_analysis/{ticker}.csv"
        returns_df = get_dividend_capture_return(ticker)
        logger.info(f"Dividend profits of '({ticker})':")
        log_dataframe_pretty(returns_df)
        s3_save_pd_dataframe(returns_df, s3_bucket, s3_key)

    return {
        "statusCode": 200,
        "body": f"Successfully saved dividend_capture_analysis to S3 bucket {s3_bucket}",
    }


if __name__ == "__main__":
    event = [
        {"Code": "ULVR.L", "Name": "Unilever"},
        {"Code": "OCN.L", "Name": "Unilever"},
        {"Code": "TEAM.L", "Name": "Team"},
    ]
    handler(event, {})
