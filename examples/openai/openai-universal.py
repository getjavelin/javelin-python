import asyncio
import json
import os
import sys

from dotenv import load_dotenv

load_dotenv()

from openai import AsyncOpenAI, OpenAI

from javelin_sdk import JavelinClient, JavelinConfig

# from openai import AzureOpenAI  # Not used, but imported for completeness


# -------------------------------
# Helper Functions
# -------------------------------


def init_sync_openai_client():
    """Initialize and return a synchronous OpenAI client."""
    try:
        # Set (and print) the OpenAI key
        openai_api_key = os.getenv("OPENAI_API_KEY")  # define your openai api key here
        print(f"Synchronous OpenAI client key: {openai_api_key}")
        return OpenAI(api_key=openai_api_key)
    except Exception as e:
        raise e


def init_javelin_client_sync(openai_client):
    """Initialize JavelinClient for synchronous usage and register the OpenAI route."""
    try:
        # Set (and print) the Javelin key
        javelin_api_key = os.getenv(
            "JAVELIN_API_KEY"
        )  # define your javelin api key here
        config = JavelinConfig(
            javelin_api_key=javelin_api_key,
        )
        client = JavelinClient(config)
        rout_name = "openai_univ"  # define your universal route name here
        client.register_openai(openai_client, route_name=rout_name)
        return client
    except Exception as e:
        raise e


def sync_openai_chat_completions(openai_client):
    """Call OpenAI's Chat Completions endpoint (synchronously)."""
    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "What is machine learning?"}],
        )
        return response.model_dump_json(indent=2)
    except Exception as e:
        raise e


def sync_openai_completions(openai_client):
    """Call OpenAI's Completions endpoint (synchronously)."""
    try:
        response = openai_client.completions.create(
            model="gpt-3.5-turbo-instruct",
            prompt="What is machine learning?",
            max_tokens=7,
            temperature=0,
        )
        return response.model_dump_json(indent=2)
    except Exception as e:
        raise e


def sync_openai_embeddings(openai_client):
    """Call OpenAI's Embeddings endpoint (synchronously)."""
    try:
        response = openai_client.embeddings.create(
            model="text-embedding-ada-002",
            input="The food was delicious and the waiter...",
            encoding_format="float",
        )
        return response.model_dump_json(indent=2)
    except Exception as e:
        raise e


def sync_openai_stream(openai_client):
    """Call OpenAI's Chat Completions endpoint with streaming."""
    try:
        stream = openai_client.chat.completions.create(
            messages=[{"role": "user", "content": "Say this is a test"}],
            model="gpt-3.5-turbo",
            stream=True,
        )
        collected_chunks = []
        for chunk in stream:
            text_chunk = chunk.choices[0].delta.content or ""
            collected_chunks.append(text_chunk)
        return "".join(collected_chunks)
    except Exception as e:
        raise e


# Async part
def init_async_openai_client():
    """Initialize and return an asynchronous OpenAI client."""
    try:
        openai_api_key = os.getenv("OPENAI_API_KEY")  # add your openai api key here
        return AsyncOpenAI(api_key=openai_api_key)
    except Exception as e:
        raise e


def init_javelin_client_async(openai_async_client):
    """Initialize JavelinClient for async usage and register the OpenAI route."""
    try:
        javelin_api_key = os.getenv("JAVELIN_API_KEY")  # add your javelin api key here
        config = JavelinConfig(javelin_api_key=javelin_api_key, base_url=os.getenv("JAVELIN_BASE_URL"))
        client = JavelinClient(config)
        client.register_openai(openai_async_client, route_name="openai_univ")
        return client
    except Exception as e:
        raise e


async def async_openai_chat_completions(openai_async_client):
    """Call OpenAI's Chat Completions endpoint (asynchronously)."""
    try:
        chat_completion = await openai_async_client.chat.completions.create(
            messages=[{"role": "user", "content": "Say this is a test"}],
            model="gpt-3.5-turbo",
        )
        return chat_completion.model_dump_json(indent=2)
    except Exception as e:
        raise e


# -------------------------------
# Main Function
# -------------------------------
def main():
    print("=== Synchronous OpenAI Example ===")
    try:
        # Initialize sync client
        openai_client = init_sync_openai_client()
        javelin_sync_client = init_javelin_client_sync(openai_client)
    except Exception as e:
        print(f"Error initializing synchronous clients: {e}")
        return

    # 1) Chat Completions
    print("\n--- OpenAI: Chat Completions ---")
    try:
        chat_completions_response = sync_openai_chat_completions(openai_client)
        if not chat_completions_response.strip():
            print("Error: Empty response failed")
        else:
            print(chat_completions_response)
    except Exception as e:
        print(f"Error in chat completions: {e}")

    # 2) Completions
    print("\n--- OpenAI: Completions ---")
    try:
        completions_response = sync_openai_completions(openai_client)
        if not completions_response.strip():
            print("Error: Empty response  failed")
        else:
            print(completions_response)
    except Exception as e:
        print(f"Error in completions: {e}")

    # 3) Embeddings
    print("\n--- OpenAI: Embeddings ---")
    try:
        embeddings_response = sync_openai_embeddings(openai_client)
        if not embeddings_response.strip():
            print("Error: Empty response  failed")
        else:
            print(embeddings_response)
    except Exception as e:
        print(f"Error in embeddings: {e}")

    # 4) Streaming
    print("\n--- OpenAI: Streaming ---")
    try:
        stream_result = sync_openai_stream(openai_client)
        if not stream_result.strip():
            print("Error: Empty response failed")
        else:
            print("stream_result", stream_result)
            print("Streaming response:", stream_result)
    except Exception as e:
        print(f"Error in streaming: {e}")

    # 5) Asynchronous Chat Completions
    print("\n=== Asynchronous OpenAI Example ===")
    try:
        openai_async_client = init_async_openai_client()
        javelin_async_client = init_javelin_client_async(openai_async_client)
    except Exception as e:
        print(f"Error initializing async clients: {e}")
        return

    print("\n--- AsyncOpenAI: Chat Completions ---")
    try:
        async_response = asyncio.run(async_openai_chat_completions(openai_async_client))
        if not async_response.strip():
            print("Error: Empty response  failed")
        else:
            print(async_response)
    except Exception as e:
        print(f"Error in async chat completions: {e}")


if __name__ == "__main__":
    main()
