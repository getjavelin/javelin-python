import os
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
from javelin_sdk import JavelinClient, JavelinConfig

load_dotenv()


def init_gemini_client():
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY is not set!")

    openai_client = OpenAI(
        api_key=gemini_api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )

    javelin_api_key = os.getenv("JAVELIN_API_KEY")
    config = JavelinConfig(javelin_api_key=javelin_api_key)
    client = JavelinClient(config)
    client.register_gemini(openai_client, route_name="google_univ")

    return openai_client


def gemini_chat_completions(client):
    response = client.chat.completions.create(
        model="gemini-1.5-flash",
        n=1,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Explain to me how AI works"},
        ],
    )
    return response


def gemini_function_calling(client):
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
                            "description": "City and state, e.g. Chicago, IL",
                        },
                        "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                    },
                    "required": ["location"],
                },
            },
        }
    ]
    messages = [
        {"role": "user", "content": "What's the weather like in Chicago today?"}
    ]
    response = client.chat.completions.create(
        model="gemini-1.5-flash", messages=messages, tools=tools, tool_choice="auto"
    )
    return response.model_dump_json(indent=2)


class CalendarEvent(BaseModel):
    name: str
    date: str
    participants: list[str]


def gemini_structured_output(client):
    completion = client.beta.chat.completions.parse(
        model="gemini-1.5-flash",
        messages=[
            {"role": "system", "content": "Extract the event information."},
            {
                "role": "user",
                "content": "John and Susan are going to an AI conference on Friday.",
            },
        ],
        response_format=CalendarEvent,
    )
    return completion.model_dump_json(indent=2)


def gemini_embeddings(client):
    response = client.embeddings.create(
        input="Your text string goes here", model="text-embedding-004"
    )
    return response.model_dump_json(indent=2)


def main():
    print("=== Gemini Example ===")
    try:
        gemini_client = init_gemini_client()
    except Exception as e:
        print(f"Error initializing Gemini client: {e}")
        return

    run_gemini_chat_completions(gemini_client)
    run_gemini_function_calling(gemini_client)
    run_gemini_structured_output(gemini_client)
    run_gemini_embeddings(gemini_client)
    print("\nScript Complete")


def run_gemini_chat_completions(gemini_client):
    print("\n--- Gemini: Chat Completions ---")
    try:
        response = gemini_chat_completions(gemini_client)
        content = response.choices[0].message.content.strip()
        preview = content[:300] + "..." if len(content) > 300 else content
        if content:
            print(f"✅ passed → {preview}")
        else:
            print("❌ failed - Empty response")
    except Exception as e:
        print(f"❌ failed - Error in chat completions: {e}")


def run_gemini_function_calling(gemini_client):
    print("\n--- Gemini: Function Calling ---")
    try:
        func_response = gemini_function_calling(gemini_client)
        print(func_response)
    except Exception as e:
        print(f"❌ failed - Error in function calling: {e}")


def run_gemini_structured_output(gemini_client):
    print("\n--- Gemini: Structured Output ---")
    try:
        structured_response = gemini_structured_output(gemini_client)
        print(structured_response)
    except Exception as e:
        print(f"❌ failed - Error in structured output: {e}")


def run_gemini_embeddings(gemini_client):
    print("\n--- Gemini: Embeddings ---")
    try:
        embeddings_response = gemini_embeddings(gemini_client)
        print(embeddings_response)
    except Exception as e:
        print(f"❌ failed - Error in embeddings: {e}")


if __name__ == "__main__":
    main()
