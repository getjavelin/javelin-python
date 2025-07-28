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
    bedrock_runtime_client = boto3.client(
        service_name="bedrock-runtime", region_name="us-east-1"
    )
    bedrock_client = boto3.client(service_name="bedrock", region_name="us-east-1")

    config = JavelinConfig(
        # Replace with your Javelin API key
        javelin_api_key=os.getenv("JAVELIN_API_KEY")
    )
    javelin_client = JavelinClient(config)
    javelin_client.register_bedrock(
        bedrock_runtime_client=bedrock_runtime_client,
        bedrock_client=bedrock_client,
        bedrock_session=None,
        route_name="amazon",
    )
    return bedrock_runtime_client


def bedrock_invoke_example(bedrock_runtime_client):
    response = bedrock_runtime_client.invoke_model(
        modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",
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
    response = bedrock_runtime_client.invoke_model(
        modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",
        body=json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 500,
                "system": "You are an economist with access to lots of data",
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            "Write an article about the impact of high inflation "
                            "on a country's GDP"
                        ),
                    }
                ],
            }
        ),
        contentType="application/json",
    )
    response_body = json.loads(response["body"].read())
    return json.dumps(response_body, indent=2)


def bedrock_invoke_stream_example(bedrock_runtime_client):
    response = bedrock_runtime_client.invoke_model(
        modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",
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
    response = bedrock_runtime_client.invoke_model(
        modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",
        body=json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 500,
                "system": "You are an economist with access to lots of data",
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            "Write an article about the impact of high inflation "
                            "on a country's GDP"
                        ),
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


def test_claude_v2_invoke(bedrock_runtime_client):
    print("\n--- Test: anthropic.claude-v2 / invoke ---")
    try:
        response = bedrock_runtime_client.invoke_model(
            modelId="anthropic.claude-v2",
            body=json.dumps(
                {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 100,
                    "messages": [
                        {"role": "user", "content": "Explain quantum computing"}
                    ],
                }
            ),
            contentType="application/json",
        )
        result = json.loads(response["body"].read())
        print(json.dumps(result, indent=2))
    except Exception as e:
        print("❌ Error:", e)


def test_claude_v2_stream(bedrock_runtime_client):
    print("\n--- Test: anthropic.claude-v2 / invoke-with-response-stream ---")
    try:
        response = bedrock_runtime_client.invoke_model_with_response_stream(
            modelId="anthropic.claude-v2",
            body=json.dumps(
                {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 100,
                    "messages": [{"role": "user", "content": "Tell me about LLMs"}],
                }
            ),
            contentType="application/json",
        )
        output = ""
        for part in response["body"]:
            chunk = json.loads(part["chunk"]["bytes"].decode())
            delta = chunk.get("delta", {}).get("text", "")
            output += delta
            print(delta, end="", flush=True)
        print("\nStreamed Output Complete.")
    except Exception as e:
        print("❌ Error:", e)


def test_haiku_v3_invoke(bedrock_runtime_client):
    print("\n--- Test: anthropic.claude-3-haiku-20240307-v1:0 / invoke ---")
    try:
        response = bedrock_runtime_client.invoke_model(
            modelId="anthropic.claude-3-haiku-20240307-v1:0",
            body=json.dumps(
                {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 100,
                    "messages": [{"role": "user", "content": "What is generative AI?"}],
                }
            ),
            contentType="application/json",
        )
        result = json.loads(response["body"].read())
        print(json.dumps(result, indent=2))
    except Exception as e:
        print("❌ Error:", e)


def test_haiku_v3_stream(bedrock_runtime_client):
    print(
        "\n--- Test: anthropic.claude-3-haiku-20240307-v1:0 / "
        "invoke-with-response-stream ---"
    )
    try:
        response = bedrock_runtime_client.invoke_model_with_response_stream(
            modelId="anthropic.claude-3-haiku-20240307-v1:0",
            body=json.dumps(
                {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 100,
                    "messages": [
                        {"role": "user", "content": "What are AI guardrails?"}
                    ],
                }
            ),
            contentType="application/json",
        )
        output = ""
        for part in response["body"]:
            chunk = json.loads(part["chunk"]["bytes"].decode())
            delta = chunk.get("delta", {}).get("text", "")
            output += delta
            print(delta, end="", flush=True)
        print("\nStreamed Output Complete.")
    except Exception as e:
        print("❌ Error:", e)


def test_bedrock_invoke(bedrock_runtime_client):
    print("\n--- Bedrock Invoke Example ---")
    try:
        invoke_resp = bedrock_invoke_example(bedrock_runtime_client)
        if not invoke_resp.strip():
            print("Error: Empty response in invoke example")
        else:
            print("Invoke Response:\n", invoke_resp)
    except Exception as e:
        print("Error in bedrock_invoke_example:", e)


def test_bedrock_converse(bedrock_runtime_client):
    print("\n--- Bedrock Converse Example ---")
    try:
        converse_resp = bedrock_converse_example(bedrock_runtime_client)
        if not converse_resp.strip():
            print("Error: Empty response in converse example")
        else:
            print("Converse Response:\n", converse_resp)
    except Exception as e:
        print("Error in bedrock_converse_example:", e)


def test_bedrock_invoke_stream(bedrock_runtime_client):
    print("\n--- Bedrock Streaming Invoke Example ---")
    try:
        invoke_stream_resp = bedrock_invoke_stream_example(bedrock_runtime_client)
        if not invoke_stream_resp.strip():
            print("Error: Empty streaming invoke response")
        else:
            print("\nStreaming Invoke Response Complete.")
    except Exception as e:
        print("Error in bedrock_invoke_stream_example:", e)


def test_bedrock_converse_stream(bedrock_runtime_client):
    print("\n--- Bedrock Streaming Converse Example ---")
    try:
        converse_stream_resp = bedrock_converse_stream_example(bedrock_runtime_client)
        if not converse_stream_resp.strip():
            print("Error: Empty streaming converse response")
        else:
            print("\nStreaming Converse Response Complete.")
    except Exception as e:
        print("Error in bedrock_converse_stream_example:", e)


def main():
    try:
        bedrock_runtime_client = init_bedrock()
    except Exception as e:
        print("Error initializing Bedrock + Javelin:", e)
        return

    test_bedrock_invoke(bedrock_runtime_client)
    test_bedrock_converse(bedrock_runtime_client)
    test_bedrock_invoke_stream(bedrock_runtime_client)
    test_bedrock_converse_stream(bedrock_runtime_client)
    run_claude_v2_tests(bedrock_runtime_client)
    run_haiku_tests(bedrock_runtime_client)
    run_titan_text_lite_test(bedrock_runtime_client)
    run_titan_text_premier_tests(bedrock_runtime_client)
    run_titan_text_premier_converse_tests(bedrock_runtime_client)
    run_cohere_command_light_tests(bedrock_runtime_client)


def run_claude_v2_tests(bedrock_runtime_client):
    # 5) Test anthropic.claude-v2 / invoke
    print("\n--- Test: anthropic.claude-v2 / invoke ---")
    try:
        response = bedrock_runtime_client.invoke_model(
            modelId="anthropic.claude-v2",
            body=json.dumps(
                {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 100,
                    "messages": [
                        {"role": "user", "content": "Explain quantum computing"}
                    ],
                }
            ),
            contentType="application/json",
        )
        result = json.loads(response["body"].read())
        print(json.dumps(result, indent=2))
    except Exception as e:
        print("Error in claude-v2 invoke:", e)

    # 6) Test anthropic.claude-v2 / invoke-with-response-stream
    print("\n--- Test: anthropic.claude-v2 / invoke-with-response-stream ---")
    try:
        response = bedrock_runtime_client.invoke_model_with_response_stream(
            modelId="anthropic.claude-v2",
            body=json.dumps(
                {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 100,
                    "messages": [{"role": "user", "content": "Tell me about LLMs"}],
                }
            ),
            contentType="application/json",
        )
        for part in response["body"]:
            chunk = json.loads(part["chunk"]["bytes"].decode())
            delta = chunk.get("delta", {}).get("text", "")
            print(delta, end="", flush=True)
        print("\nStreamed Output Complete.")
    except Exception as e:
        print("Error in claude-v2 stream:", e)


def run_haiku_tests(bedrock_runtime_client):
    # 7) Test anthropic.claude-3-haiku-20240307-v1:0 / invoke
    print("\n--- Test: anthropic.claude-3-haiku-20240307-v1:0 / invoke ---")
    try:
        response = bedrock_runtime_client.invoke_model(
            modelId="anthropic.claude-3-haiku-20240307-v1:0",
            body=json.dumps(
                {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 100,
                    "messages": [{"role": "user", "content": "What is generative AI?"}],
                }
            ),
            contentType="application/json",
        )
        result = json.loads(response["body"].read())
        print(json.dumps(result, indent=2))
    except Exception as e:
        print("Error in haiku invoke:", e)

    # 8) Test anthropic.claude-3-haiku-20240307-v1:0 / invoke-with-response-stream
    print(
        "\n--- Test: anthropic.claude-3-haiku-20240307-v1:0 / "
        "invoke-with-response-stream ---"
    )
    try:
        response = bedrock_runtime_client.invoke_model_with_response_stream(
            modelId="anthropic.claude-3-haiku-20240307-v1:0",
            body=json.dumps(
                {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 100,
                    "messages": [
                        {"role": "user", "content": "What are AI guardrails?"}
                    ],
                }
            ),
            contentType="application/json",
        )
        for part in response["body"]:
            chunk = json.loads(part["chunk"]["bytes"].decode())
            delta = chunk.get("delta", {}).get("text", "")
            print(delta, end="", flush=True)
        print("\nStreamed Output Complete.")
    except Exception as e:
        print("Error in haiku stream:", e)


def run_titan_text_lite_test(bedrock_runtime_client):
    # 9) Test amazon.titan-text-lite-v1 / invoke-with-response-stream
    print("\n--- Test: amazon.titan-text-lite-v1 / invoke-with-response-stream ---")
    try:
        response = bedrock_runtime_client.invoke_model_with_response_stream(
            modelId="amazon.titan-text-lite-v1",
            body=json.dumps({"inputText": "Test prompt for titan-lite"}),
            contentType="application/json",
        )
        for part in response["body"]:
            print(part)
        print("\nStreamed Output Complete.")
    except Exception as e:
        print("Error in titan-text-lite-v1 stream:", e)


def run_titan_text_premier_tests(bedrock_runtime_client):
    # 10–13) Test amazon.titan-text-premier-v1 across invoke types
    for mode in ["invoke", "invoke-with-response-stream"]:
        print(f"\n--- Test: amazon.titan-text-premier-v1 / {mode} ---")
        try:
            if mode == "invoke":
                response = bedrock_runtime_client.invoke_model(
                    modelId="amazon.titan-text-premier-v1",
                    body=json.dumps({"inputText": "Premier test input"}),
                    contentType="application/json",
                )
            else:
                response = bedrock_runtime_client.invoke_model_with_response_stream(
                    modelId="amazon.titan-text-premier-v1",
                    body=json.dumps({"inputText": "Premier test input"}),
                    contentType="application/json",
                )
            if "stream" in mode:
                for part in response["body"]:
                    print(part)
                print("\nStreamed Output Complete.")
            else:
                result = json.loads(response["body"].read())
                print(json.dumps(result, indent=2))
        except Exception as e:
            if "provided model identifier is invalid" in str(e):
                print(
                    "✅ Skipped amazon.titan-text-premier-v1 test "
                    "(model identifier invalid)"
                )
            else:
                print(f"Error in titan-text-premier-v1 / {mode}:", e)


def run_titan_text_premier_converse_tests(bedrock_runtime_client):
    # 11) Test amazon.titan-text-premier-v1 across converse types
    for mode in ["converse", "converse-stream"]:
        print(f"\n--- Test: amazon.titan-text-premier-v1 / {mode} ---")
        try:
            if mode == "converse":
                response = bedrock_runtime_client.converse(
                    modelId="amazon.titan-text-premier-v1",
                    messages=[
                        {
                            "role": "user",
                            "content": [{"text": "Premier converse test input"}],
                        }
                    ],
                )
                print(response)
            else:
                response = bedrock_runtime_client.converse_stream(
                    modelId="amazon.titan-text-premier-v1",
                    messages=[
                        {
                            "role": "user",
                            "content": [{"text": "Premier converse test input"}],
                        }
                    ],
                )
                for part in response["stream"]:
                    print(part)
        except Exception as e:
            if "provided model identifier is invalid" in str(e):
                print(
                    "✅ Skipped amazon.titan-text-premier-v1 test "
                    "(model identifier invalid)"
                )
            else:
                print(f"Error in titan-text-premier-v1 / {mode}:", e)


def run_cohere_command_light_tests(bedrock_runtime_client):
    # 12–14) Test cohere.command-light-text-v14 across modes
    for mode in ["invoke", "converse", "converse-stream"]:
        print(f"\n--- Test: cohere.command-light-text-v14 / {mode} ---")
        try:
            if mode == "invoke":
                response = bedrock_runtime_client.invoke_model(
                    modelId="cohere.command-light-text-v14",
                    body=json.dumps({"prompt": "Cohere light model test"}),
                    contentType="application/json",
                )
                result = json.loads(response["body"].read())
                print(json.dumps(result, indent=2))
            elif mode == "converse":
                response = bedrock_runtime_client.converse(
                    modelId="cohere.command-light-text-v14",
                    messages=[
                        {"role": "user", "content": [{"text": "Cohere converse test"}]}
                    ],
                )
                print(response)
            else:
                response = bedrock_runtime_client.converse_stream(
                    modelId="cohere.command-light-text-v14",
                    messages=[
                        {"role": "user", "content": [{"text": "Cohere converse test"}]}
                    ],
                )
                for part in response["stream"]:
                    print(part)
        except Exception as e:
            print(f"Error in cohere.command-light-text-v14 / {mode}:", e)


if __name__ == "__main__":
    main()
