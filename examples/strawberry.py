
import json
import os
import base64
import requests
import asyncio
from openai import OpenAI, AsyncOpenAI, AzureOpenAI
from javelin_sdk import JavelinClient, JavelinConfig
from pydantic import BaseModel

# Environment Variables
openai_api_key = os.getenv("OPENAI_API_KEY")
javelin_api_key = os.getenv('JAVELIN_API_KEY')
gemini_api_key = os.getenv("GEMINI_API_KEY")

# Initialize Javelin Client
config = JavelinConfig(
    base_url="https://api-dev.javelin.live",
    # base_url="http://localhost:8000",
    javelin_api_key=javelin_api_key,
)
client = JavelinClient(config)

def register_openai_client():
    openai_client = OpenAI(api_key=openai_api_key)
    client.register_openai(openai_client, route_name="openai")
    return openai_client

def openai_chat_completions():
    openai_client = register_openai_client()
    response = openai_client.chat.completions.create(
        model="o1-mini",
        messages=[{"role": "user", "content": "How many Rs are there in the word 'strawberry', 'retriever', 'mulberry', 'refrigerator'?"}],
    )
    print(response.model_dump_json(indent=2))

# Initialize Javelin Client
def initialize_javelin_client():
    javelin_api_key = os.getenv('JAVELIN_API_KEY')
    config = JavelinConfig(
        base_url="https://api-dev.javelin.live",
        javelin_api_key=javelin_api_key,
    )
    return JavelinClient(config)

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

# Gemini Chat Completions
def gemini_chat_completions(openai_client):
    response = openai_client.chat.completions.create(
        model="gemini-2.0-pro-exp",
        n=1,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "How many Rs are there in the word 'strawberry', 'retriever', 'mulberry', 'refrigerator'?"}
        ]
    )
    print(response.model_dump_json(indent=2))

def main_sync():
    openai_chat_completions()

    client = initialize_javelin_client()
    openai_client = create_gemini_client()
    register_gemini(client, openai_client)
    gemini_chat_completions(openai_client)

def main():
    main_sync()                 # Run synchronous calls

if __name__ == "__main__":
    main()