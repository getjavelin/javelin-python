#!/usr/bin/env python
import os
from dotenv import load_dotenv
from openai import OpenAI
from javelin_sdk import JavelinClient, JavelinConfig

load_dotenv()


def init_gemini_client():
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    javelin_api_key = os.getenv("JAVELIN_API_KEY")

    if not gemini_api_key or not javelin_api_key:
        raise ValueError("Missing GEMINI_API_KEY or JAVELIN_API_KEY")

    gemini_client = OpenAI(
        api_key=gemini_api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )

    config = JavelinConfig(javelin_api_key=javelin_api_key)
    client = JavelinClient(config)
    client.register_gemini(gemini_client, route_name="google_univ")

    return gemini_client


def test_function_call(client):
    print("\n==== Gemini Function Calling Test ====")
    try:
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get weather info for a given location",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {"type": "string", "description": "e.g. Tokyo"},
                            "unit": {
                                "type": "string",
                                "enum": ["celsius", "fahrenheit"],
                            },
                        },
                        "required": ["location"],
                    },
                },
            }
        ]
        messages = [
            {"role": "user", "content": "What's the weather like in Tokyo today?"}
        ]
        response = client.chat.completions.create(
            model="gemini-1.5-flash", messages=messages, tools=tools, tool_choice="auto"
        )
        print("Response:")
        print(response.model_dump_json(indent=2))
    except Exception as e:
        print(f"Function calling failed: {e}")


def test_tool_call(client):
    print("\n==== Gemini Tool Calling Test ====")
    try:
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_quote",
                    "description": "Returns a motivational quote",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "category": {
                                "type": "string",
                                "description": "e.g. success",
                            }
                        },
                        "required": [],
                    },
                },
            }
        ]
        messages = [{"role": "user", "content": "Give me a quote about perseverance."}]
        response = client.chat.completions.create(
            model="gemini-1.5-flash", messages=messages, tools=tools, tool_choice="auto"
        )
        print("Response:")
        print(response.model_dump_json(indent=2))
    except Exception as e:
        print(f"Tool calling failed: {e}")


def main():
    print("=== Gemini Javelin Tool/Function Test ===")
    try:
        gemini_client = init_gemini_client()
    except Exception as e:
        print(f"Initialization failed: {e}")
        return

    test_function_call(gemini_client)
    test_tool_call(gemini_client)


if __name__ == "__main__":
    main()
