import os
import json

# The official OpenAI Python library with Gemini support (via Javelin)
from openai import OpenAI
from javelin_sdk import JavelinClient, JavelinConfig
from pydantic import BaseModel

# -----------------------------------------------------------------------------
# 1) Initialize Gemini + Javelin
# -----------------------------------------------------------------------------
def init_gemini_client():
    """
    Sets environment variables for Gemini and Javelin, creates an OpenAI client,
    registers it with Javelin, and returns the configured client.
    """
    print("Initializing Gemini client...")

    # Hard-coded environment variable assignment (for demonstration)
    # You may prefer to do: gemini_api_key = os.environ.get("GEMINI_API_KEY") in real usage.
    os.environ["GEMINI_API_KEY"] = "" # add your gemini api key here
    gemini_api_key = os.environ["GEMINI_API_KEY"]
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY is not set!")
    print("Gemini API Key loaded successfully.")

    # Create an OpenAI client configured for Gemini
    openai_client = OpenAI(
        api_key=gemini_api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )

    # Javelin configuration
    os.environ["JAVELIN_API_KEY"] = "" # add your javelin api key here
    javelin_api_key = os.environ["JAVELIN_API_KEY"]
    config = JavelinConfig(javelin_api_key=javelin_api_key)
    client = JavelinClient(config)

    # Register the Gemini client with Javelin
    client.register_gemini(openai_client, route_name="gemini-univ")

    return openai_client


# -----------------------------------------------------------------------------
# 2) Chat Completions
# -----------------------------------------------------------------------------
def gemini_chat_completions(client):
    """
    Demonstrates a basic chat completion with Gemini.
    Returns the JSON string of the response.
    """
    response = client.chat.completions.create(
        model="gemini-1.5-flash",
        n=1,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Explain to me how AI works"}
        ]
    )
    return response.model_dump_json(indent=2)


# -----------------------------------------------------------------------------
# 3) Streaming
# -----------------------------------------------------------------------------
def gemini_streaming(client):
    """
    Demonstrates streaming a response from Gemini.
    Returns a concatenated string of all streamed tokens for demonstration.
    """
    response = client.chat.completions.create(
        model="gemini-1.5-flash",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"}
        ],
        stream=True
    )

    # Accumulate partial content in a list
    streamed_content = []
    for chunk in response:
        if chunk.choices and chunk.choices[0].delta:
            delta_content = chunk.choices[0].delta
            # Just store the dictionary or the text portion.
            # We'll store the entire dict as JSON for demonstration:
            streamed_content.append(json.dumps(delta_content))

    # Join all chunk data with newlines
    return "\n".join(streamed_content)


# -----------------------------------------------------------------------------
# 4) Function calling
# -----------------------------------------------------------------------------
def gemini_function_calling(client):
    """
    Demonstrates a function-calling scenario with Gemini (like OpenAI Tools).
    Returns JSON string of the response.
    """
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get the weather in a given location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state, e.g. Chicago, IL",
                        },
                        "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                    },
                    "required": ["location"],
                },
            }
        }
    ]
    messages = [{"role": "user", "content": "What's the weather like in Chicago today?"}]
    response = client.chat.completions.create(
        model="gemini-1.5-flash",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )
    return response.model_dump_json(indent=2)


# -----------------------------------------------------------------------------
# 5) Structured output
# -----------------------------------------------------------------------------
class CalendarEvent(BaseModel):
    name: str
    date: str
    participants: list[str]

def gemini_structured_output(client):
    """
    Demonstrates how to request structured JSON output from Gemini
    using the 'parse' endpoint (beta).
    Returns the JSON string of the structured result.
    """
    completion = client.beta.chat.completions.parse(
        model="gemini-1.5-flash",
        messages=[
            {"role": "system", "content": "Extract the event information."},
            {"role": "user", "content": "John and Susan are going to an AI conference on Friday."},
        ],
        response_format=CalendarEvent,
    )
    return completion.model_dump_json(indent=2)


# -----------------------------------------------------------------------------
# 6) Embeddings
# -----------------------------------------------------------------------------
def gemini_embeddings(client):
    """
    Demonstrates generating embeddings using Gemini.
    Returns the JSON string of the embeddings response.
    """
    response = client.embeddings.create(
        input="Your text string goes here",
        model="text-embedding-004"
    )
    return response.model_dump_json(indent=2)


# -----------------------------------------------------------------------------
# 7) Main
# -----------------------------------------------------------------------------
def main():
    # 1. Initialize the Gemini (PaLM) client via Javelin
    try:
        gemini_client = init_gemini_client()
    except Exception as e:
        print("Error initializing Gemini client:", e)
        return

    print("\nGemini: 1 - Chat completions")
    try:
        chat_response = gemini_chat_completions(gemini_client)
        print(chat_response)
    except Exception as e:
        print("Error in chat completions:", e)

    print("\nGemini: 2 - Streaming")
    try:
        stream_response = gemini_streaming(gemini_client)
        print("Streaming output:")
        print(stream_response)
    except Exception as e:
        print("Error in streaming:", e)

    print("\nGemini: 3 - Function calling")
    try:
        func_response = gemini_function_calling(gemini_client)
        print(func_response)
    except Exception as e:
        print("Error in function calling:", e)

    # (Commented out) Gemini Image Understanding Example:
    # If you want, create a function `gemini_image_understanding()`
    # and call it similarly in a try/except block here.

    print("\nGemini: 4 - Structured output")
    try:
        structured_response = gemini_structured_output(gemini_client)
        print(structured_response)
    except Exception as e:
        print("Error in structured output:", e)

    print("\nGemini: 5 - Embeddings")
    try:
        embeddings_response = gemini_embeddings(gemini_client)
        print(embeddings_response)
    except Exception as e:
        print("Error in embeddings:", e)

    print("\n--- Script complete. ---")


# -----------------------------------------------------------------------------
# 8) Run main if executed directly
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    main()
