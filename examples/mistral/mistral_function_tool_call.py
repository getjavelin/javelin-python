#!/usr/bin/env python
import os
import dotenv
from langchain.chat_models import init_chat_model

dotenv.load_dotenv()

def init_mistral_model():
    return init_chat_model(
        model_name="mistral-large-latest",
        model_provider="openai",
        base_url=f"{os.getenv('JAVELIN_BASE_URL')}/v1",
        extra_headers={
            "x-javelin-route": "mistral_univ",
            "x-api-key": os.environ.get("OPENAI_API_KEY"),
            "Authorization": f"Bearer {os.environ.get('MISTRAL_API_KEY')}"
        }
    )

def run_basic_prompt(model):
    print("\n==== Mistral Prompt Test ====")
    try:
        response = model.invoke("Write a haiku about sunrise.")
        print("Response:\n", response)
    except Exception as e:
        print("Prompt failed:", e)

def run_function_calling(model):
    print("\n==== Mistral Function Calling Test ====")
    try:
        messages = [{"role": "user", "content": "Get the current weather in Mumbai"}]
        functions = [
            {
                "name": "get_weather",
                "description": "Fetch current weather",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string", "description": "City name"},
                        "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
                    },
                    "required": ["location"]
                }
            }
        ]
        response = model.predict_messages(messages=messages, functions=functions, function_call="auto")
        print("Function Response:\n", response)
    except Exception as e:
        print("Function calling failed:", e)

def run_tool_calling(model):
    print("\n==== Mistral Tool Calling Test ====")
    try:
        messages = [{"role": "user", "content": "Tell me a motivational quote"}]
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_quote",
                    "description": "Returns a motivational quote",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "category": {"type": "string", "description": "e.g. life, success"}
                        },
                        "required": []
                    }
                }
            }
        ]
        response = model.predict_messages(messages=messages, tools=tools, tool_choice="auto")
        print("Tool Response:\n", response)
    except Exception as e:
        print("Tool calling failed:", e)

def main():
    try:
        model = init_mistral_model()
    except Exception as e:
        print(f"Failed to initialize model: {e}")
        return

    run_basic_prompt(model)
    run_function_calling(model)
    run_tool_calling(model)

if __name__ == "__main__":
    main()
