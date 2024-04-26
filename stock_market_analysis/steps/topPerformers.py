"""Get top performers of companies."""

def handler(event: dict, context: dict):  # noqa: ARG001
    """Handle lambda requestes."""
    print("Hello World from topPerformers")
    return {
        "statusCode": 200,
        "body": "Hello World from topPerformers"
    }
