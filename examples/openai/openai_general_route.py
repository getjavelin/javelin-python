from openai import OpenAI, AsyncOpenAI
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()


# -------------------------------
# Client Initialization
# -------------------------------


def init_sync_openai_client():
    """Initialize and return a synchronous OpenAI client with Javelin headers."""
    try:
        openai_api_key = os.getenv("OPENAI_API_KEY")
        javelin_api_key = os.getenv("JAVELIN_API_KEY")
        javelin_headers = {"x-api-key": javelin_api_key}
        print(f"[DEBUG] Synchronous OpenAI client key: {openai_api_key}")
        # This client is configured for chat completions.
        return OpenAI(
            api_key=openai_api_key,
            base_url=f"{os.getenv('JAVELIN_BASE_URL')}/v1/query/openai",
            default_headers=javelin_headers,
        )
    except Exception as e:
        raise e


def init_async_openai_client():
    """Initialize and return an asynchronous OpenAI client with Javelin headers."""
    try:
        openai_api_key = os.getenv("OPENAI_API_KEY")
        javelin_api_key = os.getenv("JAVELIN_API_KEY")
        javelin_headers = {"x-api-key": javelin_api_key}
        return AsyncOpenAI(
            api_key=openai_api_key,
            base_url="https://api-dev.javelin.live/v1/query/openai",
            default_headers=javelin_headers,
        )
    except Exception as e:
        raise e


# -------------------------------
# Synchronous Helper Functions
# -------------------------------


def sync_openai_regular_non_stream(openai_client):
    """Call the chat completions endpoint (synchronously) using a regular
    (non-streaming) request."""
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful assistant that translates English to French."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "AI has the power to transform humanity and make the world "
                        "a better place"
                    ),
                },
            ],
        )
        return response.model_dump_json(indent=2)
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


def sync_openai_embeddings(_):
    """Call OpenAI's Embeddings endpoint (synchronously) using a dedicated
    embeddings client.

    This function creates a new OpenAI client instance pointing to the
    embeddings endpoint.
    """
    try:
        openai_api_key = os.getenv("OPENAI_API_KEY")
        javelin_api_key = os.getenv("JAVELIN_API_KEY")
        javelin_headers = {"x-api-key": javelin_api_key}
        # Create a new client instance for embeddings.
        embeddings_client = OpenAI(
            api_key=openai_api_key,
            base_url=(
                "https://api-dev.javelin.live/v1/query/openai_embeddings"
            ),
            default_headers=javelin_headers,
        )
        response = embeddings_client.embeddings.create(
            model="text-embedding-3-small",
            input="The food was delicious and the waiter...",
        )
        return response.model_dump_json(indent=2)
    except Exception as e:
        raise e


def sync_openai_stream(openai_client):
    """Call OpenAI's Chat Completions endpoint with streaming enabled
    (synchronously)."""
    try:
        stream = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say this is a test"}],
            stream=True,
        )
        collected_chunks = []
        for chunk in stream:
            text_chunk = chunk.choices[0].delta.content or ""
            collected_chunks.append(text_chunk)
        return "".join(collected_chunks)
    except Exception as e:
        raise e


# -------------------------------
# Asynchronous Helper Functions
# -------------------------------


async def async_openai_regular_non_stream(openai_async_client):
    """Call the chat completions endpoint asynchronously using a regular
    (non-streaming) request."""
    try:
        response = await openai_async_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful assistant that translates English to French."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "AI has the power to transform humanity and make the world "
                        "a better place"
                    ),
                },
            ],
        )
        return response.model_dump_json(indent=2)
    except Exception as e:
        raise e


async def async_openai_chat_completions(openai_async_client):
    """Call OpenAI's Chat Completions endpoint asynchronously."""
    try:
        chat_completion = await openai_async_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say this is a test"}],
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
        openai_client = init_sync_openai_client()
    except Exception as e:
        print(f"[DEBUG] Error initializing synchronous client: {e}")
        return

    run_sync_tests(openai_client)
    run_async_tests()


def run_sync_tests(openai_client):
    run_regular_non_stream_test(openai_client)
    run_chat_completions_test(openai_client)
    run_embeddings_test(openai_client)
    run_stream_test(openai_client)


def run_regular_non_stream_test(openai_client):
    print("\n--- Regular Non-Streaming Chat Completion ---")
    try:
        regular_response = sync_openai_regular_non_stream(openai_client)
        if not regular_response.strip():
            print("[DEBUG] Error: Empty regular response")
        else:
            print(regular_response)
    except Exception as e:
        print(f"[DEBUG] Error in regular non-stream chat completion: {e}")


def run_chat_completions_test(openai_client):
    print("\n--- Chat Completions ---")
    try:
        chat_response = sync_openai_chat_completions(openai_client)
        if not chat_response.strip():
            print("[DEBUG] Error: Empty chat completions response")
        else:
            print(chat_response)
    except Exception as e:
        print(f"[DEBUG] Error in chat completions: {e}")


def run_embeddings_test(openai_client):
    print("\n--- Embeddings ---")
    try:
        embeddings_response = sync_openai_embeddings(openai_client)
        if not embeddings_response.strip():
            print("[DEBUG] Error: Empty embeddings response")
        else:
            print(embeddings_response)
    except Exception as e:
        print(f"[DEBUG] Error in embeddings: {e}")


def run_stream_test(openai_client):
    print("\n--- Streaming ---")
    try:
        stream_result = sync_openai_stream(openai_client)
        if not stream_result.strip():
            print("[DEBUG] Error: Empty stream response")
        else:
            print("[DEBUG] Streaming response:", stream_result)
    except Exception as e:
        print(f"[DEBUG] Error in streaming: {e}")


def run_async_tests():
    print("\n=== Asynchronous OpenAI Example ===")
    try:
        openai_async_client = init_async_openai_client()
    except Exception as e:
        print(f"[DEBUG] Error initializing async client: {e}")
        return

    run_async_regular_test(openai_async_client)
    run_async_chat_test(openai_async_client)


def run_async_regular_test(openai_async_client):
    print("\n--- Async Regular Non-Streaming Chat Completion ---")
    try:
        async_regular_response = asyncio.run(
            async_openai_regular_non_stream(openai_async_client)
        )
        if not async_regular_response.strip():
            print("[DEBUG] Error: Empty async regular response")
        else:
            print(async_regular_response)
    except Exception as e:
        print(f"[DEBUG] Error in async regular non-stream chat completion: {e}")


def run_async_chat_test(openai_async_client):
    print("\n--- Async Chat Completions ---")
    try:
        async_chat_response = asyncio.run(
            async_openai_chat_completions(openai_async_client)
        )
        if not async_chat_response.strip():
            print("[DEBUG] Error: Empty async chat response")
        else:
            print(async_chat_response)
    except Exception as e:
        print(f"[DEBUG] Error in async chat completions: {e}")


if __name__ == "__main__":
    main()
