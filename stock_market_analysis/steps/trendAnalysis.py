"""Get top performers of companies."""
import json


def handler(event: dict, context: dict):  # noqa: ARG001
    """Print the batch of pairs received from the event."""
    print("Received batch:", json.dumps(event))
    return {"statusCode": 200, "body": f"Processed {len(event)} pairs"}
