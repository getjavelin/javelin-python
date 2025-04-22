#!/usr/bin/env python
import os
import json
import re
import argparse
from dotenv import load_dotenv
from openai import OpenAI, AzureOpenAI
from javelin_sdk import JavelinClient, JavelinConfig, RouteNotFoundError

# Load environment variables once at the start
load_dotenv()

# ---------------------------
# OpenAI – Unified Endpoint Examples
# ---------------------------
def init_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    return OpenAI(api_key=api_key)

def init_javelin_client(openai_client, route_name="openai_univ"):
    javelin_api_key = os.getenv("JAVELIN_API_KEY")
    config = JavelinConfig(javelin_api_key=javelin_api_key)
    client = JavelinClient(config)
    client.register_openai(openai_client, route_name=route_name)
    return client

def openai_function_call_non_stream():
    print("\n==== Running OpenAI Non-Streaming Function Calling Example ====")
    client = init_openai_client()
    init_javelin_client(client)
    response = client.chat.completions.create(
        model="o3-mini",  # Latest o1 model
        messages=[
            {"role": "user", "content": "What is the current weather in New York?"}
        ],
        functions=[
            {
                "name": "get_current_weather",
                "description": "Retrieves current weather information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "City and state (e.g., New York, NY)"
                        },
                        "unit": {
                            "type": "string",
                            "enum": ["celsius", "fahrenheit"]
                        }
                    },
                    "required": ["location"]
                }
            }
        ],
        function_call="auto"
    )
    print("OpenAI Non-Streaming Response:")
    print(response.model_dump_json(indent=2))

def openai_function_call_stream():
    print("\n==== Running OpenAI Streaming Function Calling Example ====")
    client = init_openai_client()
    init_javelin_client(client)
    stream = client.chat.completions.create(
        model="o3-mini",
        messages=[
            {"role": "user", "content": "Tell me a fun fact and then call a function."}
        ],
        functions=[
            {
                "name": "tell_fun_fact",
                "description": "Returns a fun fact",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "fact": {
                            "type": "string",
                            "description": "A fun fact about the topic"
                        }
                    },
                    "required": ["fact"]
                }
            }
        ],
        function_call="auto",
        stream=True
    )
    collected = []
    print("OpenAI Streaming Response:")
    for chunk in stream:
        delta = chunk.choices[0].delta
        print(chunk)
        if hasattr(delta, "content") and delta.content:
            collected.append(delta.content)
    print("".join(collected))

def openai_structured_output_call_generic():
    print("\n==== Running OpenAI Structured Output Function Calling Example ====")
    openai_client = init_openai_client()
    init_javelin_client(openai_client)
    messages = [
        {
            "role": "system",
            "content": "You are an assistant that always responds in valid JSON format without any additional text."
        },
        {
            "role": "user",
            "content": (
                "Provide a generic example of structured data output in JSON format. "
                "The JSON should include the keys: 'id', 'name', 'description', "
                "and 'attributes' (which should be a nested object with arbitrary key-value pairs)."
            )
        }
    ]
    
    response = openai_client.chat.completions.create(
        model="o3-mini",  # can use o1 model as well
        messages=messages,
    )
    
    print("Structured Output (JSON) Response:")
    print(response.model_dump_json(indent=2))
    
    try:
        reply_content = response.choices[0].message.content
    except (IndexError, AttributeError) as e:
        print("Error extracting message content:", e)
        reply_content = ""
    
    try:
        json_output = json.loads(reply_content)
        print("\nParsed JSON Output:")
        print(json.dumps(json_output, indent=2))
    except Exception as e:
        print("\nFailed to parse JSON output. Error:", e)
        print("Raw content:", reply_content)

# ---------------------------
# Azure OpenAI – Unified Endpoint Examples
# ---------------------------
def init_azure_client():
    azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
    return AzureOpenAI(
        api_version="2023-07-01-preview",
        azure_endpoint="https://javelinpreview.openai.azure.com",
        api_key=azure_api_key
    )

def init_javelin_client_azure(azure_client, route_name="azureopenai_univ"):
    javelin_api_key = os.getenv("JAVELIN_API_KEY")
    config = JavelinConfig(javelin_api_key=javelin_api_key)
    client = JavelinClient(config)
    client.register_azureopenai(azure_client, route_name=route_name)
    return client

def azure_function_call_non_stream():
    print("\n==== Running Azure OpenAI Non-Streaming Function Calling Example ====")
    azure_client = init_azure_client()
    init_javelin_client_azure(azure_client)
    response = azure_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": "Schedule a meeting at 10 AM tomorrow."}
        ],
        functions=[
            {
                "name": "schedule_meeting",
                "description": "Schedules a meeting in the calendar",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "time": {"type": "string", "description": "Meeting time (ISO format)"},
                        "date": {"type": "string", "description": "Meeting date (YYYY-MM-DD)"}
                    },
                    "required": ["time", "date"]
                }
            }
        ],
        function_call="auto"
    )
    print("Azure OpenAI Non-Streaming Response:")
    print(response.to_json())

def azure_function_call_stream():
    print("\n==== Running Azure OpenAI Streaming Function Calling Example ====")
    azure_client = init_azure_client()
    init_javelin_client_azure(azure_client)
    stream = azure_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": "Schedule a meeting at 10 AM tomorrow."}
        ],
        functions=[
            {
                "name": "schedule_meeting",
                "description": "Schedules a meeting in the calendar",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "time": {"type": "string", "description": "Meeting time (ISO format)"},
                        "date": {"type": "string", "description": "Meeting date (YYYY-MM-DD)"}
                    },
                    "required": ["time", "date"]
                }
            }
        ],
        function_call="auto",
        stream=True
    )
    print("Azure OpenAI Streaming Response:")
    for chunk in stream:
        print(chunk)

def extract_json_from_markdown(text: str) -> str:
    """
    Extracts JSON content from a markdown code block if present.
    Removes leading and trailing triple backticks.
    """
    match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if match:
        return match.group(1)
    return text.strip()

def azure_structured_output_call():
    print("\n==== Running Azure OpenAI Structured Output Function Calling Example ====")
    azure_client = init_azure_client()
    init_javelin_client_azure(azure_client)
    messages = [
        {
            "role": "system",
            "content": "You are an assistant that always responds in valid JSON format without any additional text."
        },
        {
            "role": "user",
            "content": (
                "Provide structured data in JSON format. "
                "The JSON should contain the following keys: 'id' (integer), 'title' (string), "
                "'description' (string), and 'metadata' (a nested object with arbitrary key-value pairs)."
            )
        }
    ]
    
    response = azure_client.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )
    
    print("Structured Output (JSON) Response:")
    print(response.to_json())
    
    try:
        reply_content = response.choices[0].message.content
        reply_content_clean = extract_json_from_markdown(reply_content)
        json_output = json.loads(reply_content_clean)
        print("\nParsed JSON Output:")
        print(json.dumps(json_output, indent=2))
    except Exception as e:
        print("\nFailed to parse JSON output. Error:", e)
        print("Raw content:", reply_content)

# ---------------------------
# OpenAI – Regular Route Endpoint Examples
# ---------------------------
def openai_regular_non_stream():
    print("\n==== Running OpenAI Regular Route Non-Streaming Function Calling Example ====")
    javelin_api_key = os.getenv('JAVELIN_API_KEY')
    llm_api_key = os.getenv("OPENAI_API_KEY")
    if not javelin_api_key or not llm_api_key:
        raise ValueError("Both JAVELIN_API_KEY and OPENAI_API_KEY must be set.")
    print("OpenAI LLM API Key:", llm_api_key)
    config = JavelinConfig(
        base_url="https://api-dev.javelin.live",
        javelin_api_key=javelin_api_key,
        llm_api_key=llm_api_key,
    )
    client = JavelinClient(config)
    print("Successfully connected to Javelin Client for OpenAI")
    
    query_data = {
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that translates English to French."},
            {"role": "user", "content": "AI has the power to transform humanity and make the world a better place."},
        ]
    }
    
    try:
        response = client.query_route("openai", query_data)
        print("Response from OpenAI Regular Endpoint:")
        print(response)
    except RouteNotFoundError:
        print("Route 'openai' Not Found")
    except Exception as e:
        print("Error querying OpenAI endpoint:", e)

def openai_regular_stream():
    print("\n==== Running OpenAI Regular Route Streaming Function Calling Example ====")
    javelin_api_key = os.getenv('JAVELIN_API_KEY')
    llm_api_key = os.getenv("OPENAI_API_KEY")
    if not javelin_api_key or not llm_api_key:
        raise ValueError("Both JAVELIN_API_KEY and OPENAI_API_KEY must be set.")
    config = JavelinConfig(
        base_url="https://api-dev.javelin.live",
        javelin_api_key=javelin_api_key,
        llm_api_key=llm_api_key,
    )
    client = JavelinClient(config)
    print("Successfully connected to Javelin Client for OpenAI")
    
    query_data = {
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that translates English to French."},
            {"role": "user", "content": "AI has the power to transform humanity and make the world a better place."},
        ],
        "functions": [
            {
                "name": "translate_text",
                "description": "Translates English text to French",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to translate"
                        }
                    },
                    "required": ["text"]
                }
            }
        ],
        "function_call": "auto",
        "stream": True
    }
    
    try:
        response = client.query_route("openai", query_data)
        print("Response from OpenAI Regular Endpoint (Streaming):")
        if query_data.get("stream"):
            for chunk in response:
                print(chunk)
        else:
            print(response)
    except RouteNotFoundError as e:
        print(f"Route 'openai' not found: {str(e)}")
    except Exception as e:
        print(f"Error occurred while getting response: {str(e)}")


# ---------------------------
# Main function and argument parsing
# ---------------------------
def main():
    parser = argparse.ArgumentParser(description="Run Unified Endpoint Examples")
    parser.add_argument(
        "--example",
        type=str,
        default="all",
        choices=[
            "all", "openai_non_stream", "openai_stream", "openai_structured",
            "azure_non_stream", "azure_stream", "azure_structured",
            "openai_regular_non_stream", "openai_regular_stream"
        ],
        help="The example to run (or 'all' to run every example)"
    )
    args = parser.parse_args()

    if args.example == "all":
        openai_function_call_non_stream()
        openai_function_call_stream()
        openai_structured_output_call_generic()
        azure_function_call_non_stream()
        azure_function_call_stream()
        azure_structured_output_call()
        openai_regular_non_stream()
        openai_regular_stream()
    elif args.example == "openai_non_stream":
        openai_function_call_non_stream()
    elif args.example == "openai_stream":
        openai_function_call_stream()
    elif args.example == "openai_structured":
        openai_structured_output_call_generic()
    elif args.example == "azure_non_stream":
        azure_function_call_non_stream()
    elif args.example == "azure_stream":
        azure_function_call_stream()
    elif args.example == "azure_structured":
        azure_structured_output_call()
    elif args.example == "openai_regular_non_stream":
        openai_regular_non_stream()
    elif args.example == "openai_regular_stream":
        openai_regular_stream()

if __name__ == "__main__":
    main()