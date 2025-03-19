import json
import os
import base64
import requests
import asyncio
from openai import OpenAI, AsyncOpenAI, AzureOpenAI
from javelin_sdk import JavelinClient, JavelinConfig
from pydantic import BaseModel

# Environment Variables
javelin_base_url = os.getenv("JAVELIN_BASE_URL")
openai_api_key = os.getenv("OPENAI_API_KEY")
javelin_api_key = os.getenv('JAVELIN_API_KEY')
gemini_api_key = os.getenv("GEMINI_API_KEY")

# Global JavelinClient, used for everything
config = JavelinConfig(
    base_url=javelin_base_url,
    javelin_api_key=javelin_api_key,
)
client = JavelinClient(config) # Global JavelinClient

# Initialize Javelin Client
def initialize_javelin_client():
    config = JavelinConfig(
        base_url=javelin_base_url,
        javelin_api_key=javelin_api_key,
    )
    return JavelinClient(config)

def register_openai_client():
    openai_client = OpenAI(api_key=openai_api_key)
    client.register_openai(openai_client, route_name="openai")
    return openai_client

def openai_chat_completions():
    openai_client = register_openai_client()
    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "What is machine learning?"}],
    )
    print(response.model_dump_json(indent=2))

def openai_completions():
    openai_client = register_openai_client()
    response = openai_client.completions.create(
        model="gpt-3.5-turbo-instruct",
        prompt="What is machine learning?",
        max_tokens=7,
        temperature=0
    )
    print(response.model_dump_json(indent=2))

def openai_embeddings():
    openai_client = register_openai_client()
    response = openai_client.embeddings.create(
        model="text-embedding-ada-002",
        input="The food was delicious and the waiter...",
        encoding_format="float"
    )
    print(response.model_dump_json(indent=2))

def openai_streaming_chat():
    openai_client = register_openai_client()
    stream = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Say this is a test"}],
        stream=True,
    )
    for chunk in stream:
        print(chunk.choices[0].delta.content or "", end="")

def register_async_openai_client():
    openai_async_client = AsyncOpenAI(api_key=openai_api_key)
    client.register_openai(openai_async_client, route_name="openai")
    return openai_async_client

async def async_openai_chat_completions():
    openai_async_client = register_async_openai_client()
    response = await openai_async_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Say this is a test"}],
    )
    print(response.model_dump_json(indent=2))

async def async_openai_streaming_chat():
    openai_async_client = register_async_openai_client()
    stream = await openai_async_client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Say this is a test"}],
        stream=True,
    )
    async for chunk in stream:
        print(chunk.choices[0].delta.content or "", end="")

# Create Gemini client
def create_gemini_client():
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    return OpenAI(
        api_key=gemini_api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )

# Register Gemini client with Javelin
def register_gemini(client, openai_client):
    client.register_gemini(openai_client, route_name="openai")

# Function to download and encode the image
def encode_image_from_url(image_url):
    response = requests.get(image_url)
    if response.status_code == 200:
        return base64.b64encode(response.content).decode('utf-8')
    else:
        raise Exception(f"Failed to download image: {response.status_code}")

# Gemini Chat Completions
def gemini_chat_completions(openai_client):
    response = openai_client.chat.completions.create(
        model="gemini-1.5-flash",
        n=1,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Explain to me how AI works"}
        ]
    )
    print(response.model_dump_json(indent=2))

# Gemini Streaming Chat Completions
def gemini_streaming_chat(openai_client):
    stream = openai_client.chat.completions.create(
        model="gemini-1.5-flash",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"}
        ],
        stream=True
    )
    '''
    for chunk in response:
        print(chunk.choices[0].delta)
    '''
    
    for chunk in stream:
        print(chunk.choices[0].delta.content or "", end="")

# Gemini Function Calling
def gemini_function_calling(openai_client):
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get the weather in a given location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string", "description": "The city and state, e.g. Chicago, IL"},
                        "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                    },
                    "required": ["location"],
                },
            }
        }
    ]

    messages = [{"role": "user", "content": "What's the weather like in Chicago today?"}]
    response = openai_client.chat.completions.create(
        model="gemini-1.5-flash",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )
    print(response.model_dump_json(indent=2))

# Gemini Image Understanding
def gemini_image_understanding(openai_client):
    image_url = "https://storage.googleapis.com/cloud-samples-data/generative-ai/image/scones.jpg"
    base64_image = encode_image_from_url(image_url)

    response = openai_client.chat.completions.create(
        model="gemini-1.5-flash",
        messages=[
            {"role": "user", "content": [
                {"type": "text", "text": "What is in this image?"},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
            ]}
        ]
    )
    print(response.model_dump_json(indent=2))

# Gemini Structured Output
def gemini_structured_output(openai_client):
    class CalendarEvent(BaseModel):
        name: str
        date: str
        participants: list[str]

    completion = openai_client.beta.chat.completions.parse(
        model="gemini-1.5-flash",
        messages=[
            {"role": "system", "content": "Extract the event information."},
            {"role": "user", "content": "John and Susan are going to an AI conference on Friday."}
        ],
        response_format=CalendarEvent,
    )
    print(completion.model_dump_json(indent=2))

# Gemini Embeddings
def gemini_embeddings(openai_client):
    response = openai_client.embeddings.create(
        input="Your text string goes here",
        model="text-embedding-004"
    )
    print(response.model_dump_json(indent=2))

# Create Azure OpenAI client
def create_azureopenai_client():
    azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
    return AzureOpenAI(
        api_version="2023-07-01-preview", 
        azure_endpoint="https://javelinpreview.openai.azure.com"
    )

# Register Azure OpenAI client with Javelin
def register_azureopenai(client, openai_client):
    client.register_azureopenai(openai_client, route_name="openai")

# Azure OpenAI Scenario
def azure_openai_chat_completions(openai_client):
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "How do I output all files in a directory using Python?"}]
    )
    print(response.model_dump_json(indent=2))

# Create DeepSeek client
def create_deepseek_client():
    deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
    return OpenAI(
        api_key=deepseek_api_key, 
        base_url="https://api.deepseek.com"
    )

# Register DeepSeek client with Javelin
def register_deepseek(client, openai_client):
    client.register_deepseek(openai_client, route_name="openai")

# DeepSeek Chat Completions
def deepseek_chat_completions(openai_client):
    response = openai_client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Hello"}
        ],
        stream=False
    )
    print(response.model_dump_json(indent=2))

# DeepSeek Reasoning Model
def deepseek_reasoning_model(openai_client):
    # deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
    # openai_client = OpenAI(api_key=deepseek_api_key, base_url="https://api.deepseek.com")

    # Round 1
    messages = [{"role": "user", "content": "9.11 and 9.8, which is greater?"}]
    response = openai_client.chat.completions.create(model="deepseek-reasoner", messages=messages)
    print(response.to_json())

    content = response.choices[0].message.content

    # Round 2
    messages.append({"role": "assistant", "content": content})
    messages.append({"role": "user", "content": "How many Rs are there in the word 'strawberry'?"})
    response = openai_client.chat.completions.create(model="deepseek-reasoner", messages=messages)

    print(response.to_json())

# Mistral Chat Completions
def mistral_chat_completions():
    mistral_api_key = os.getenv("MISTRAL_API_KEY")
    openai_client = OpenAI(api_key=mistral_api_key, base_url="https://api.mistral.ai/v1")

    chat_response = openai_client.chat.completions.create(
        model="mistral-large-latest",
        messages=[{"role": "user", "content": "What is the best French cheese?"}]
    )
    print(chat_response.to_json())

def main_sync():
    openai_chat_completions()
    openai_completions()
    openai_embeddings()
    openai_streaming_chat()

    print ("\n")
    
    openai_client = create_azureopenai_client()
    register_azureopenai(client, openai_client)

    azure_openai_chat_completions(openai_client)
    
    openai_client = create_gemini_client()
    register_gemini(client, openai_client)

    gemini_chat_completions(openai_client)
    gemini_streaming_chat(openai_client)
    gemini_function_calling(openai_client)
    gemini_image_understanding(openai_client)
    gemini_structured_output(openai_client)
    gemini_embeddings(openai_client)

    '''
    # Pending: model specs, uncomment after model is available
    openai_client = create_deepseek_client()
    register_deepseek(client, openai_client)
    # deepseek_chat_completions(openai_client)

    # deepseek_reasoning_model(openai_client)
    '''

    '''
    mistral_chat_completions()
    '''
    
async def main_async():
    await async_openai_chat_completions()
    print("\n")
    await async_openai_streaming_chat()
    print("\n")

def main():
    main_sync()                 # Run synchronous calls
    # asyncio.run(main_async())   # Run asynchronous calls within a single event loop

if __name__ == "__main__":
    main()
