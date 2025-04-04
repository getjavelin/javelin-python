#!/usr/bin/env python3
import boto3
import json
import os
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# -------------------------------
# Utility Function
# -------------------------------
def extract_final_text(json_str: str) -> str:
    """
    Attempt to parse the JSON string, then:
      1) If 'completion' exists, return it (typical from invoke).
      2) Else if 'messages' exists, return the last assistant message (typical from converse).
      3) Otherwise, return the entire JSON string.
    """
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError:
        return json_str  # Not valid JSON, return as-is

    # Typical 'invoke' result
    if "completion" in data:
        return data["completion"]

    # Typical 'converse' result
    if "messages" in data and data["messages"]:
        last_msg = data["messages"][-1]
        pieces = []
        for item in last_msg.get("content", []):
            if isinstance(item, dict) and "text" in item:
                pieces.append(item["text"])
        return "\n".join(pieces) if pieces else "No assistant reply found."

    # Default
    return json_str

# -------------------------------
# Bedrock Client Setup
# -------------------------------
def get_bedrock_client():
    """
    Initialize the Bedrock client with custom headers. 
    Credentials and the Javelin (Bedrock) API Key can come from environment variables or .env file.
    """
    try:
        load_dotenv()

        aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID", "YOUR_ACCESS_KEY")
        aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY", "YOUR_SECRET_KEY")
        bedrock_api_key = os.getenv("JAVELIN_API_KEY", "YOUR_BEDROCK_API_KEY")

        custom_headers = {'x-api-key': bedrock_api_key}

        client = boto3.client(
            service_name="bedrock-runtime",
            region_name="us-east-1",
            endpoint_url=os.path.join(os.getenv("JAVELIN_BASE_URL"), "v1"),
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )

        def add_custom_headers(request, **kwargs):
            request.headers.update(custom_headers)

        client.meta.events.register('before-send.*.*', add_custom_headers)
        return client
    except Exception as e:
        raise Exception(f"Failed to create Bedrock client: {str(e)}")


# -------------------------------
# Invoke (Non-Streaming)
# -------------------------------
def call_bedrock_model_invoke(client, route_name, input_text):
    """
    Non-streaming call. 
    Prompt must start with '\n\nHuman:' and end with '\n\nAssistant:' per route requirement.
    """
    try:
        body = {
            "prompt": f"\n\nHuman: Compose a haiku about {input_text}\n\nAssistant:",
            "max_tokens_to_sample": 1000,
            "temperature": 0.7
        }
        body_bytes = json.dumps(body).encode("utf-8")
        response = client.invoke_model(
            modelId=route_name,
            body=body_bytes,
            contentType="application/json",
        )
        return response["body"].read().decode("utf-8", errors="replace")
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]
        status_code = e.response["ResponseMetadata"]["HTTPStatusCode"]
        raise Exception(f"ClientError: {error_code} - {error_message} (HTTP {status_code})")
    except Exception as e:
        raise Exception(f"Unexpected error in invoke: {str(e)}")

# -------------------------------
# Converse (Non-Streaming)
# -------------------------------
def call_bedrock_model_converse(client, route_name, user_topic):
    """
    Non-streaming call. 
    Roles must be 'user' or 'assistant'. The user role includes the required prompt structure.
    """
    try:
        response = client.converse(
            modelId=route_name,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "text": f"\n\nHuman: Compose a haiku about {user_topic}\n\nAssistant:"
                        }
                    ]
                }
            ],
            inferenceConfig={
                "maxTokens": 300,
                "temperature": 0.7
            }
        )
        # Return as JSON so we can parse it in extract_final_text
        return json.dumps(response)
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]
        status_code = e.response["ResponseMetadata"]["HTTPStatusCode"]
        raise Exception(f"ClientError: {error_code} - {error_message} (HTTP {status_code})")
    except Exception as e:
        raise Exception(f"Unexpected error in converse: {str(e)}")


# -------------------------------
# Main Testing Script
# -------------------------------
def main():
    print("=== Synchronous Bedrock Testing For general Rout ===")

    # 1) Create a Bedrock client
    try:
        bedrock_client = get_bedrock_client()
    except Exception as e:
        print(f"Error initializing Bedrock client: {e}")
        return

    # 2) Invoke (non-streaming)
    print("\n--- Bedrock: Invoke (non-streaming) ---")
    try:
        route_invoke = "claude_haiku_invoke"  # Adjust if your route name differs
        input_text_invoke = "sunset on a winter evening"
        raw_invoke_output = call_bedrock_model_invoke(bedrock_client, route_invoke, input_text_invoke)
        final_invoke_text = extract_final_text(raw_invoke_output)
        print(final_invoke_text)
    except Exception as e:
        print(e)

    # 3) Converse (non-streaming)
    print("\n--- Bedrock: Converse (non-streaming) ---")
    try:
        route_converse = "claude_haiku_converse"  # Adjust if your route name differs
        user_topic = "a tranquil mountain pond"
        raw_converse_output = call_bedrock_model_converse(bedrock_client, route_converse, user_topic)
        final_converse_text = extract_final_text(raw_converse_output)
        print(final_converse_text)
    except Exception as e:
        print(e)

if __name__ == "__main__":
    main()
