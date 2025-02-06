import json
import os
from openai import OpenAI
import dotenv
from javelin_sdk import (
    JavelinClient,
    JavelinConfig,
)

javelin_api_key = os.getenv('JAVELIN_API_KEY')
llm_api_key = os.getenv("OPENAI_API_KEY")

# Create OpenAI client
openai_client = OpenAI(api_key=llm_api_key)

# Initialize Javelin Client
config = JavelinConfig(
    # base_url="https://api-dev.javelin.live",
    base_url="http://localhost:8000",
    javelin_api_key=javelin_api_key,
)
client = JavelinClient(config)
client.register_openai(openai_client, route_name="openai")

# Call OpenAI endpoints
chat_completions = openai_client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "What is machine learning?"}],
)
print(chat_completions.model_dump_json(indent=2))

completions = openai_client.completions.create(
    model="gpt-3.5-turbo-instruct",
    prompt="What is machine learning?",
    max_tokens=7,
    temperature=0
)
print(completions.model_dump_json(indent=2))

embeddings = openai_client.embeddings.create(
    model="text-embedding-ada-002",
    input="The food was delicious and the waiter...",
    encoding_format="float"
)
print(embeddings.model_dump_json(indent=2))
