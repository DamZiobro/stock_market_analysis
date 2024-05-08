"""Get top performers of companies."""

import json

import pandas as pd

from stock_market_analysis.src.logger import logger
from stock_market_analysis.src.stock_data_fetcher import fetch_historic_dividends
from stock_market_analysis.src.utils import log_dataframe_pretty


def calculate_dividend_day_investment_returns(
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


def handler(event: list[dict[str, str]], context: dict):  # noqa: ARG001
    """Handle lambda requestes."""
    logger.info(
        "Analysis of historical dividend profit based on pre-ex-dividend-date purchase."
    )
    logger.info("event: %s", json.dumps(event))

    HL_BUY_AND_SELL_COST = 2 * 11.95  # noqa: N806

    for item in event:
        ticker = item["Code"] + ".L"
        company_name = item["Name"]
        dividends_df = fetch_historic_dividends(ticker, limit=10)
        if dividends_df is None:
            logger.info(
                f"Company '{company_name} ({ticker})' doesn't have dividend history."
            )
            continue

        returns_df = calculate_dividend_day_investment_returns(
            dividends_df, transactions_fees=HL_BUY_AND_SELL_COST
        )
        logger.info(f"Dividend profits of '{company_name} ({ticker})':")
        log_dataframe_pretty(returns_df)

    # dividends = fetch_historic_dividends(ticker, limit)
    return {"statusCode": 200, "body": "Hello World from historyDividendAnalysis"}


if __name__ == "__main__":
    event = [
        {"Code": "ULVR", "Name": "Unilever"},
        {"Code": "TEAM", "Name": "Team"},
    ]
    handler(event, {})
