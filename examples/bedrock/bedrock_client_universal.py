import json
import os

import boto3
from dotenv import load_dotenv

from javelin_sdk import JavelinClient, JavelinConfig

load_dotenv()


def init_bedrock():
    """
    1) Configure Bedrock clients using boto3,
    2) Register them with Javelin (optional but often recommended),
    3) Return the bedrock_runtime_client for direct 'invoke_model' calls.
    """
    # Configure the bedrock-runtime and bedrock service clients
    bedrock_runtime_client = boto3.client(
        service_name="bedrock-runtime", region_name="us-west-2"
    )
    bedrock_client = boto3.client(service_name="bedrock", region_name="us-west-2")

    # Initialize Javelin Client (if you want the route registered)
    config = JavelinConfig(
        javelin_api_key=os.getenv("JAVELIN_API_KEY"), # Replace with your Javelin API key
        base_url=os.getenv("JAVELIN_BASE_URL")
    )
    javelin_client = JavelinClient(config)

    # Register the bedrock clients with Javelin under route "bedrock"
    javelin_client.register_bedrock(
        bedrock_runtime_client=bedrock_runtime_client,
        bedrock_client=bedrock_client,
        route_name="amazon_univ",
    )
    return bedrock_runtime_client


def bedrock_invoke_example(bedrock_runtime_client):
    """
    Demonstrates a basic 'invoke' style call (non-streaming).
    Returns a JSON-formatted string of the response.
    """
    response = bedrock_runtime_client.invoke_model(
        modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",  # Example model ID
        body=json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 100,
                "messages": [{"role": "user", "content": "What is machine learning?"}],
            }
        ),
        contentType="application/json",
    )

    response_body = json.loads(response["body"].read())
    return json.dumps(response_body, indent=2)


def bedrock_converse_example(bedrock_runtime_client):
    """
    Demonstrates a 'converse' style call by including 'system' text plus a user message.
    Still uses 'invoke_model', but the request body includes additional fields.
    """
    response = bedrock_runtime_client.invoke_model(
        modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",
        body=json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 500,
                "system": [
                    {"type": "text", "text": "You are an economist with access to lots of data"}
                ],
                "messages": [
                    {
                        "role": "user",
                        "content": [{"type": "text", "text": "Write an article about the impact of high inflation on a country's GDP"}]
                    }
                ],
            }
        ),
        contentType="application/json",
    )

    response_body = json.loads(response["body"].read())
    return json.dumps(response_body, indent=2)



def bedrock_invoke_stream_example(bedrock_runtime_client):
    """
    Demonstrates a streaming 'invoke' call by processing the response tokens as they arrive.
    Iterates over the streaming response lines and prints them in real-time.
    """
    response = bedrock_runtime_client.invoke_model(
        modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",  # Example model ID
        body=json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 100,
                "messages": [{"role": "user", "content": "What is machine learning?"}],
            }
        ),
        contentType="application/json",
    )
    tokens = []
    try:
        for line in response["body"].iter_lines():
            if line:
                decoded_line = line.decode("utf-8")
                tokens.append(decoded_line)
                print(decoded_line, end="", flush=True)
    except Exception as e:
        print("Error streaming invoke response:", e)
    return "".join(tokens)


def bedrock_converse_stream_example(bedrock_runtime_client):
    """
    Demonstrates a streaming 'converse' call by processing the response tokens as they arrive.
    Iterates over the streaming response lines for a conversation style input.
    """
    response = bedrock_runtime_client.invoke_model(
        modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",
        body=json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 500,
                "system": [
                    {"type": "text", "text": "You are an economist with access to lots of data"}
                ],
                "messages": [
                    {
                        "role": "user",
                        "content": [{"type": "text", "text": "Write an article about the impact of high inflation on a country's GDP"}]
                    }
                ],
            }
        ),
        contentType="application/json",
    )
    tokens = []
    try:
        for line in response["body"].iter_lines():
            if line:
                decoded_line = line.decode("utf-8")
                tokens.append(decoded_line)
                print(decoded_line, end="", flush=True)
    except Exception as e:
        print("Error streaming converse response:", e)
    return "".join(tokens)


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
        if not invoke_resp.strip():
            print("Error: Empty response in invoke example")
        else:
            print("Invoke Response:\n", invoke_resp)
    except Exception as e:
        print("Error in bedrock_invoke_example:", e)

    # 2) 'Converse' style
    print("\n--- Bedrock Converse Example ---")
    try:
        converse_resp = bedrock_converse_example(bedrock_runtime_client)
        if not converse_resp.strip():
            print("Error: Empty response in converse example")
        else:
            print("Converse Response:\n", converse_resp)
    except Exception as e:
        print("Error in bedrock_converse_example:", e)

    # 3) Streaming Invoke Example
    print("\n--- Bedrock Streaming Invoke Example ---")
    try:
        invoke_stream_resp = bedrock_invoke_stream_example(bedrock_runtime_client)
        if not invoke_stream_resp.strip():
            print("Error: Empty streaming invoke response")
        else:
            print("\nStreaming Invoke Response Complete.")
    except Exception as e:
        print("Error in bedrock_invoke_stream_example:", e)

    # 4) Streaming Converse Example
    print("\n--- Bedrock Streaming Converse Example ---")
    try:
        converse_stream_resp = bedrock_converse_stream_example(bedrock_runtime_client)
        if not converse_stream_resp.strip():
            print("Error: Empty streaming converse response")
        else:
            print("\nStreaming Converse Response Complete.")
    except Exception as e:
        print("Error in bedrock_converse_stream_example:", e)

    print("\nScript complete.")


if __name__ == "__main__":
    main()
