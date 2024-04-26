def handler(event, context):
    print("Hello World from fetchData")
    return {
        'statusCode': 200,
        'body': "Hello World from fetchData"
    }
