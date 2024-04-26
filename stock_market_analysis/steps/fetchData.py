"""Fetching companies codes from CSV file and return as JSON."""
import csv
from pathlib import Path
from typing import List

from pydantic import BaseModel, FilePath


class CSVData(BaseModel):
    """Model of Code<->Name association."""

    Code: str
    Name: str


def read_csv(file_path: FilePath) -> List[CSVData]:
    """Read a CSV file and converts it to a list of CSVData.

    :param file_path: Path to the CSV file.
    :return: List of CSVData instances.
    """
    data_list = []
    with Path(file_path).open(newline="", encoding="utf-8") as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            data_list.append(CSVData(**row))
    return data_list


def handler(event: dict, context: dict) -> list:  # noqa: ARG001
    """AWS Lambda function to process CSV file to JSON.

    :param event: Lambda event.
    :param context: Lambda context.
    :return: JSON response.
    """
    #TODO(damian): pass the BATCH_SIZE from serverless.yml vars  # noqa: TD003
    BATCH_SIZE = 20  # noqa: N806

    pwd = Path(__file__).parent.parent
    csv_file_path = pwd / "data" / "ftse.csv"
    data = read_csv(csv_file_path)
    code_name_records = [item.dict() for item in data]
    return [
        code_name_records[i : i + BATCH_SIZE] for i in range(0, len(code_name_records), BATCH_SIZE)
    ]  # Split data into batches of 20
