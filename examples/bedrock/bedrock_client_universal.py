import boto3
import os
import json
from javelin_sdk import JavelinClient, JavelinConfig
from dotenv import load_dotenv

load_dotenv()

def init_bedrock():
    """
    1) Configure Bedrock clients using boto3,
    2) Register them with Javelin (optional but often recommended),
    3) Return the bedrock_runtime_client for direct 'invoke_model' calls.
    """
    # Configure the bedrock-runtime and bedrock service clients
    bedrock_runtime_client = boto3.client(
        service_name="bedrock-runtime",
        region_name="us-east-1"
    )
    bedrock_client = boto3.client(
        service_name="bedrock",
        region_name="us-east-1"
    )

    # Initialize Javelin Client (if you want the route registered)
    config = JavelinConfig(
        # base_url="https://api-dev.javelin.live/v1",
        javelin_api_key=os.getenv("JAVELIN_API_KEY") # add your javelin api key here
    )
    javelin_client = JavelinClient(config)

    # Register the bedrock clients with Javelin under route "bedrock"
    javelin_client.register_bedrock(
        bedrock_runtime_client=bedrock_runtime_client,
        bedrock_client=bedrock_client,
        route_name="bedrock"
    )
    return bedrock_runtime_client

def bedrock_invoke_example(bedrock_runtime_client):
    """
    Demonstrates a basic 'invoke' style call (non-streaming).
    Returns a JSON-formatted string of the response.
    """
    response = bedrock_runtime_client.invoke_model(
        modelId="anthropic.claude-3-sonnet-20240229-v1:0",  # Example model ID
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 100,
            "messages": [
                {"role": "user", "content": "What is machine learning?"}
            ]
        }),
        contentType="application/json"
    )

    response_body = json.loads(response["body"].read())
    return json.dumps(response_body, indent=2)


def bedrock_converse_example(bedrock_runtime_client):
    """
    Demonstrates a 'converse' style call by including 'system' text plus a user message.
    Still uses 'invoke_model', but the request body includes additional fields.
    """
    response = bedrock_runtime_client.invoke_model(
        modelId="anthropic.claude-3-sonnet-20240229-v1:0",  # Example model ID
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 500,
            # 'system' text for instructions/context
            "system": [
                {"text": "You are an economist with access to lots of data"}
            ],
            # 'messages' containing the user content
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "text": "Write an article about impact of high inflation to GDP of a country"
                        }
                    ]
                }
            ]
        }),
        contentType="application/json"
    )

    response_body = json.loads(response["body"].read())
    return json.dumps(response_body, indent=2)


def main():
    try:
        bedrock_runtime_client = init_bedrock()
    except Exception as e:
        print("Error initializing Bedrock + Javelin:", e)
        return

    # 1) Basic 'invoke'
    print("\n--- Bedrock Invoke Example ---")
    try:
        invoke_resp = bedrock_invoke_example(bedrock_runtime_client)
        print("Invoke Response:\n", invoke_resp)
    except Exception as e:
        print("Error in bedrock_invoke_example:", e)

    # 2) 'Converse' style
    print("\n--- Bedrock Converse Example ---")
    try:
        converse_resp = bedrock_converse_example(bedrock_runtime_client)
        print("Converse Response:\n", converse_resp)
    except Exception as e:
        print("Error in bedrock_converse_example:", e)

    print("\n--- Script complete. ---")


if __name__ == "__main__":
    main()
