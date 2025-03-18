#!/usr/bin/env python3
import os
import asyncio
from dotenv import load_dotenv
from openai import AzureOpenAI, AsyncOpenAI

# -------------------------------
# Synchronous Testing Functions
# -------------------------------

def init_azure_client_sync():
    """Initialize a synchronous AzureOpenAI client for chat, completions, and streaming."""
    try:
        llm_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        javelin_api_key = os.getenv("JAVELIN_API_KEY")
        if not llm_api_key or not javelin_api_key:
            raise Exception("AZURE_OPENAI_API_KEY and JAVELIN_API_KEY must be set in your .env file.")
        javelin_headers = {"x-api-key": javelin_api_key}
        client = AzureOpenAI(
            api_key=llm_api_key,
            base_url="https://api-dev.javelin.live/v1/query/azure-openai",
            default_headers=javelin_headers,
            api_version="2024-02-15-preview"
        )
        print(f"Synchronous AzureOpenAI client key: {llm_api_key}")
        return client
    except Exception as e:
        raise Exception(f"Error in init_azure_client_sync: {e}")

def init_azure_embeddings_client_sync():
    """Initialize a synchronous AzureOpenAI client for embeddings."""
    try:
        llm_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        javelin_api_key = os.getenv("JAVELIN_API_KEY")
        if not llm_api_key or not javelin_api_key:
            raise Exception("AZURE_OPENAI_API_KEY and JAVELIN_API_KEY must be set in your .env file.")
        javelin_headers = {"x-api-key": javelin_api_key}
        client = AzureOpenAI(
            api_key=llm_api_key,
            base_url="https://api-dev.javelin.live/v1/query/azure_ada_embeddings",
            default_headers=javelin_headers,
            api_version="2023-09-15-preview"
        )
        print("Synchronous AzureOpenAI Embeddings client initialized.")
        return client
    except Exception as e:
        raise Exception(f"Error in init_azure_embeddings_client_sync: {e}")

def sync_chat_completions(client):
    """Call the chat completions endpoint synchronously."""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Hello, you are a helpful scientific assistant."},
                {"role": "user", "content": "What is the chemical composition of sugar?"}
            ]
        )
        return response.model_dump_json(indent=2)
    except Exception as e:
        raise Exception(f"Chat completions error: {e}")

def sync_embeddings(embeddings_client):
    """Call the embeddings endpoint synchronously."""
    try:
        response = embeddings_client.embeddings.create(
            model="text-embedding-ada-002",
            input="The quick brown fox jumps over the lazy dog.",
            encoding_format="float"
        )
        return response.model_dump_json(indent=2)
    except Exception as e:
        raise Exception(f"Embeddings endpoint error: {e}")

def sync_stream(client):
    """Call the chat completions endpoint in streaming mode synchronously."""
    try:
        stream = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Generate a short poem about nature."}],
            stream=True
        )
        collected_chunks = []
        for chunk in stream:
            try:
                # Only access choices if present and nonempty
                if hasattr(chunk, "choices") and chunk.choices and len(chunk.choices) > 0:
                    try:
                        text_chunk = chunk.choices[0].delta.content or ""
                    except (IndexError, AttributeError):
                        text_chunk = ""
                else:
                    text_chunk = ""
                collected_chunks.append(text_chunk)
            except Exception:
                collected_chunks.append("")
        return "".join(collected_chunks)
    except Exception as e:
        raise Exception(f"Streaming endpoint error: {e}")

# -------------------------------
# Asynchronous Testing Functions
# -------------------------------

async def init_async_azure_client():
    """Initialize an asynchronous AzureOpenAI client for chat completions."""
    try:
        llm_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        javelin_api_key = os.getenv("JAVELIN_API_KEY")
        if not llm_api_key or not javelin_api_key:
            raise Exception("AZURE_OPENAI_API_KEY and JAVELIN_API_KEY must be set in your .env file.")
        javelin_headers = {"x-api-key": javelin_api_key}
        # Include the API version in the base URL for the async client.
        client = AsyncOpenAI(
            api_key=llm_api_key,
            base_url="https://api-dev.javelin.live/v1/query/azure-openai?api-version=2024-02-15-preview",
            default_headers=javelin_headers
        )
        return client
    except Exception as e:
        raise Exception(f"Error in init_async_azure_client: {e}")

async def async_chat_completions(client):
    """Call the chat completions endpoint asynchronously."""
    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Hello, you are a helpful scientific assistant."},
                {"role": "user", "content": "What is the chemical composition of sugar?"}
            ]
        )
        return response.model_dump_json(indent=2)
    except Exception as e:
        raise Exception(f"Async chat completions error: {e}")

# -------------------------------
# Main Function
# -------------------------------

def main():
    load_dotenv()  # Load environment variables from .env file

    print("=== Synchronous AzureOpenAI Testing ===")
    try:
        client = init_azure_client_sync()
    except Exception as e:
        print(f"Error initializing synchronous AzureOpenAI client: {e}")
        return

    # 1) Chat Completions
    print("\n--- AzureOpenAI: Chat Completions ---")
    try:
        chat_response = sync_chat_completions(client)
        if not chat_response.strip():
            print("Error: Empty chat completions response")
        else:
            print(chat_response)
    except Exception as e:
        print(e)

    # 2) Embeddings (using dedicated embeddings client)
    print("\n--- AzureOpenAI: Embeddings ---")
    try:
        embeddings_client = init_azure_embeddings_client_sync()
        embeddings_response = sync_embeddings(embeddings_client)
        if not embeddings_response.strip():
            print("Error: Empty embeddings response")
        else:
            print(embeddings_response)
    except Exception as e:
        print(e)

    # 3) Streaming
    print("\n--- AzureOpenAI: Streaming ---")
    try:
        stream_response = sync_stream(client)
        if not stream_response.strip():
            print("Error: Empty streaming response")
        else:
            print("Streaming response:", stream_response)
    except Exception as e:
        print(e)

    # 4) Asynchronous Chat Completions
    print("\n=== Asynchronous AzureOpenAI Testing ===")
    try:
        async_client = asyncio.run(init_async_azure_client())
    except Exception as e:
        print(f"Error initializing asynchronous AzureOpenAI client: {e}")
        return

    print("\n--- Async AzureOpenAI: Chat Completions ---")
    try:
        async_response = asyncio.run(async_chat_completions(async_client))
        if not async_response.strip():
            print("Error: Empty asynchronous chat completions response")
        else:
            print(async_response)
    except Exception as e:
        print(e)

if __name__ == "__main__":
    main()
