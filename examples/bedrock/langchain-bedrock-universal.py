import boto3
import os
from javelin_sdk import JavelinClient, JavelinConfig
from dotenv import load_dotenv

load_dotenv()

# This import is from the "langchain_community" extension package
# Make sure to install it:
#   pip install git+https://github.com/hwchase17/langchain.git@<some_version>#subdirectory=plugins/langchain-community
from langchain_community.llms.bedrock import Bedrock as BedrockLLM


def init_bedrock():
    """
    1) Configure Bedrock clients via boto3,
    2) Register them with Javelin,
    3) Return the bedrock_runtime_client for direct usage in LangChain.
    """
    # Create Bedrock boto3 clients
    bedrock_runtime_client = boto3.client(
        service_name="bedrock-runtime",
        region_name="us-east-1"
    )
    bedrock_client = boto3.client(
        service_name="bedrock",
        region_name="us-east-1"
    )

    # Initialize Javelin client
    config = JavelinConfig(
        javelin_api_key=os.getenv("JAVELIN_API_KEY")  # add your Javelin API key here
    )
    javelin_client = JavelinClient(config)

    # Register them with the route "bedrock" (optional but recommended)
    javelin_client.register_bedrock(
        bedrock_runtime_client=bedrock_runtime_client,
        bedrock_client=bedrock_client,
        route_name="amazon_univ"
    )

    return bedrock_runtime_client


#
# 1) Non-Streaming Example
#
def bedrock_langchain_non_stream(bedrock_runtime_client) -> str:
    """
    Demonstrates a single prompt with a synchronous, non-streaming response.
    """
    # Create the Bedrock LLM
    llm = BedrockLLM(
        client=bedrock_runtime_client,
        model_id="anthropic.claude-v2:1",  # Example model ID
        model_kwargs={
            "max_tokens_to_sample": 256,
            "temperature": 0.7,
        }
    )
    # Call the model with a single string prompt
    prompt = "What is machine learning?"
    response = llm(prompt)
    return response


#
# 2) Streaming Example (Single-Prompt)
#
def bedrock_langchain_stream(bedrock_runtime_client) -> str:
    """
    Demonstrates streaming partial responses from Bedrock.
    Returns the concatenated final text.
    """
    llm = BedrockLLM(
        client=bedrock_runtime_client,
        model_id="anthropic.claude-v2:1",
        model_kwargs={
            "max_tokens_to_sample": 256,
            "temperature": 0.7,
        }
    )

    prompt = "Tell me a short joke."
    stream_gen = llm.stream(prompt)

    collected_chunks = []
    for chunk in stream_gen:
        collected_chunks.append(chunk)
        # Optional live printing:
        print(chunk, end="", flush=True)

    return "".join(collected_chunks)


#
# 3) Converse Example (Non-Streaming)
#
def bedrock_langchain_converse(bedrock_runtime_client) -> str:
    """
    Simulates a 'system' plus 'user' message in one call.
    Because the Bedrock LLM interface accepts a single prompt string,
    we'll combine them.
    """
    llm = BedrockLLM(
        client=bedrock_runtime_client,
        model_id="anthropic.claude-v2:1",
        model_kwargs={
            "max_tokens_to_sample": 500,
            "temperature": 0.7,
        }
    )

    system_text = "You are an economist with access to lots of data."
    user_text = "Write an article about the impact of high inflation on GDP."
    combined_prompt = f"System: {system_text}\nUser: {user_text}\n"

    response = llm(combined_prompt)
    return response


#
# 4) Converse Example (Streaming)
#
def bedrock_langchain_converse_stream(bedrock_runtime_client) -> str:
    """
    Demonstrates streaming a converse-style call.
    Combines system and user messages into one prompt, then streams the response.
    """
    llm = BedrockLLM(
        client=bedrock_runtime_client,
        model_id="anthropic.claude-v2:1",
        model_kwargs={
            "max_tokens_to_sample": 500,
            "temperature": 0.7,
        }
    )

    system_text = "You are an economist with access to lots of data."
    user_text = "Write an article about the impact of high inflation on GDP."
    combined_prompt = f"System: {system_text}\nUser: {user_text}\n"

    stream_gen = llm.stream(combined_prompt)
    collected_chunks = []
    for chunk in stream_gen:
        collected_chunks.append(chunk)
        print(chunk, end="", flush=True)
    return "".join(collected_chunks)


def main():
    try:
        bedrock_runtime_client = init_bedrock()
    except Exception as e:
        print("Error initializing Bedrock + Javelin:", e)
        return

    print("\n--- LangChain Non-Streaming Example ---")
    try:
        resp_non_stream = bedrock_langchain_non_stream(bedrock_runtime_client)
        if not resp_non_stream.strip():
            print("Error: Empty response failed")
        else:
            print("Response:\n", resp_non_stream)
    except Exception as e:
        print("Error in non-stream example:", e)

    print("\n--- LangChain Streaming Example (Single-Prompt) ---")
    try:
        resp_stream = bedrock_langchain_stream(bedrock_runtime_client)
        if not resp_stream.strip():
            print("Error: Empty response failed")
        else:
            print("\nFinal Combined Streamed Text:\n", resp_stream)
    except Exception as e:
        print("Error in streaming example:", e)

    print("\n--- LangChain Converse Example (Non-Streaming) ---")
    try:
        resp_converse = bedrock_langchain_converse(bedrock_runtime_client)
        if not resp_converse.strip():
            print("Error: Empty response failed")
        else:
            print("Converse Response:\n", resp_converse)
    except Exception as e:
        print("Error in converse example:", e)

    print("\n--- LangChain Converse Example (Streaming) ---")
    try:
        resp_converse_stream = bedrock_langchain_converse_stream(bedrock_runtime_client)
        if not resp_converse_stream.strip():
            print("Error: Empty response failed")
        else:
            print("\nFinal Combined Streamed Converse Text:\n", resp_converse_stream)
    except Exception as e:
        print("Error in streaming converse example:", e)

    print("\nScript Complete.")


if __name__ == "__main__":
    main()
