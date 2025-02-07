import json
import os
import sys
import asyncio
from openai import OpenAI
from openai import AsyncOpenAI
from openai import AzureOpenAI
import dotenv
from javelin_sdk import (
    JavelinClient,
    JavelinConfig,
)

# Create OpenAI client
openai_api_key = os.getenv("OPENAI_API_KEY")
openai_client = OpenAI(api_key=openai_api_key)

# Initialize Javelin Client
javelin_api_key = os.getenv('JAVELIN_API_KEY')
config = JavelinConfig(
    base_url="https://api-dev.javelin.live",
    # base_url="http://localhost:8000",
    javelin_api_key=javelin_api_key,
)
client = JavelinClient(config)
client.register_openai(openai_client, route_name="openai")

# Call OpenAI endpoints
print("OpenAI: 1 - Chat completions")

chat_completions = openai_client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "What is machine learning?"}],
)
print(chat_completions.model_dump_json(indent=2))

print("OpenAI: 2 - Completions")

completions = openai_client.completions.create(
    model="gpt-3.5-turbo-instruct",
    prompt="What is machine learning?",
    max_tokens=7,
    temperature=0
)
print(completions.model_dump_json(indent=2))

print("OpenAI: 3 - Embeddings")

embeddings = openai_client.embeddings.create(
    model="text-embedding-ada-002",
    input="The food was delicious and the waiter...",
    encoding_format="float"
)
print(embeddings.model_dump_json(indent=2))

print("OpenAI: 4 - Streaming")

stream = openai_client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "Say this is a test",
        }
    ],
    model="gpt-4o",
    stream=True,
)
for chunk in stream:
    print(chunk.choices[0].delta.content or "", end="")

# Prints two blank lines
print("\n\n")

print("AsyncOpenAI: 5 - Chat completions")

# Create AsyncOpenAI client
openai_async_client = AsyncOpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),  # This is the default and can be omitted
)

javelin_api_key = os.getenv('JAVELIN_API_KEY')
config = JavelinConfig(
    base_url="https://api-dev.javelin.live",
    # base_url="http://localhost:8000",
    javelin_api_key=javelin_api_key,
)
client = JavelinClient(config)
client.register_openai(openai_async_client, route_name="openai")

async def main() -> None:
    chat_completion = await openai_async_client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": "Say this is a test",
            }
        ],
        model="gpt-4o",
    )
    print(chat_completion.model_dump_json(indent=2))

asyncio.run(main())

'''
print("AsyncOpenAI: 6 - Streaming")

async def main():
    stream = await openai_async_client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Say this is a test"}],
        stream=True,
    )
    async for chunk in stream:
        print(chunk.choices[0].delta.content or "", end="")

asyncio.run(main())
'''

# Prints two blank lines
print("\n\n")

# Gemini APIs
gemini_api_key = os.getenv("GEMINI_API_KEY")

# Create OpenAI client
openai_client = OpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

# Initialize Javelin Client
config = JavelinConfig(
    base_url="https://api-dev.javelin.live",
    # base_url="http://localhost:8000",
    javelin_api_key=javelin_api_key,
)
client = JavelinClient(config)
client.register_gemini(openai_client, route_name="openai")

print("Gemini: 1 - Chat completions")

response = openai_client.chat.completions.create(
    model="gemini-1.5-flash",
    n=1,
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {
            "role": "user",
            "content": "Explain to me how AI works"
        }
    ]
)

# print(response.choices[0].message)
print(response.model_dump_json(indent=2))

print("Gemini: 2 - Streaming")

response = openai_client.chat.completions.create(
  model="gemini-1.5-flash",
  messages=[
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"}
  ],
  stream=True
)

for chunk in response:
    print(chunk.choices[0].delta)

print("Gemini: 3 - Function calling")

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
response = openai_client.chat.completions.create(
  model="gemini-1.5-flash",
  messages=messages,
  tools=tools,
  tool_choice="auto"
)

print(response.model_dump_json(indent=2))

'''
print ("Gemini: 4 - Image understanding")

import base64

# Function to encode the image
def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

# Getting the base64 string
base64_image = encode_image("Path/to/agi/image.jpeg")

response = client.chat.completions.create(
  model="gemini-1.5-flash",
  messages=[
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "What is in this image?",
        },
        {
          "type": "image_url",
          "image_url": {
            "url":  f"data:image/jpeg;base64,{base64_image}"
          },
        },
      ],
    }
  ],
)

print(response.model_dump_json(indent=2))
'''

print("Gemini: 5 - Structured output")

from pydantic import BaseModel

class CalendarEvent(BaseModel):
    name: str
    date: str
    participants: list[str]

completion = openai_client.beta.chat.completions.parse(
    model="gemini-1.5-flash",
    messages=[
        {"role": "system", "content": "Extract the event information."},
        {"role": "user", "content": "John and Susan are going to an AI conference on Friday."},
    ],
    response_format=CalendarEvent,
)

print(completion.model_dump_json(indent=2))

print("Gemini: 6 - Embeddings")

response = openai_client.embeddings.create(
    input="Your text string goes here",
    model="text-embedding-004"
)

print(response.model_dump_json(indent=2))

# Prints two blank lines
print("\n\n")

'''
print("Azure OpenAI: 1 - Chat completions")

# Create AzureOpenAI client
# gets the API Key from environment variable AZURE_OPENAI_API_KEY
openai_client = AzureOpenAI(
    # https://learn.microsoft.com/azure/ai-services/openai/reference#rest-api-versioning
    api_version="2023-07-01-preview",
    # https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource?pivots=web-portal#create-a-resource
    azure_endpoint="https://javelinpreview.openai.azure.com",
)

# Initialize Javelin Client
config = JavelinConfig(
    # base_url="https://api-dev.javelin.live",
    base_url="http://localhost:8000",
    javelin_api_key=javelin_api_key,
)
client = JavelinClient(config)
client.register_azureopenai(openai_client, route_name="openai")

completion = openai_client.chat.completions.create(
    model="gpt-4o-mini",  # e.g. gpt-35-instant
    messages=[
        {
            "role": "user",
            "content": "How do I output all files in a directory using Python?",
        },
    ],
)
print(completion.to_json())
'''

'''
# print("DeepSeek: 1 - Chat completions")

deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")

# Create OpenAI client
openai_client = OpenAI(api_key=deepseek_api_key, base_url="https://api.deepseek.com")

# Initialize Javelin Client
config = JavelinConfig(
    # base_url="https://api-dev.javelin.live",
    base_url="http://localhost:8000",
    javelin_api_key=javelin_api_key,
)

# client = JavelinClient(config)
# client.register_deepseek(openai_client, route_name="openai")

response = openai_client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Hello"},
    ],
    stream=False
)

print(response.to_json())

print("DeepSeek: 2 - Reasoning Model")

deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
openai_client = OpenAI(api_key=deepseek_api_key, base_url="https://api.deepseek.com")

# Round 1
messages = [{"role": "user", "content": "9.11 and 9.8, which is greater?"}]
response = openai_client.chat.completions.create(
    model="deepseek-reasoner",
    messages=messages
)
print(response.to_json())

reasoning_content = response.choices[0].message.reasoning_content
content = response.choices[0].message.content

# Round 2
messages.append({'role': 'assistant', 'content': content})
messages.append({'role': 'user', 'content': "How many Rs are there in the word 'strawberry'?"})
response = openai_client.chat.completions.create(
    model="deepseek-reasoner",
    messages=messages
)

print(response.to_json())

'''

'''
# Create OpenAI client
mistral_api_key = os.getenv("MISTRAL_API_KEY")
openai_client = OpenAI(api_key=mistral_api_key, base_url="https://api.mistral.ai/v1")
chat_response = openai_client.chat.completions.create(
    model="mistral-large-latest",
    messages = [
        {
            "role": "user",
            "content": "What is the best French cheese?",
        },
    ]
)
print(chat_response.to_json())
'''
