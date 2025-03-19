import json
import os
import boto3
import dotenv
from javelin_sdk import (
    JavelinClient,
    JavelinConfig,
)

dotenv.load_dotenv()

# Retrieve environment variables
javelin_api_key = os.getenv("JAVELIN_API_KEY")

# Initialize Bedrock Client
bedrockruntime_client = boto3.client(
    service_name="bedrock-runtime",
    region_name="us-east-1"
)

# Initialize Bedrock Client
bedrock_client = boto3.client(
    service_name="bedrock",
    region_name="us-east-1"
)

# Initialize Javelin Client
config = JavelinConfig(
    base_url="https://api-dev.javelin.live",
    javelin_api_key=javelin_api_key,
)
client = JavelinClient(config)
client.register_bedrock(bedrockruntime_client, bedrock_client, route_name="bedrock")

# Call Bedrock Model
response = bedrockruntime_client.invoke_model(
                modelId="anthropic.claude-3-sonnet-20240229-v1:0",
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 100,
                    "messages": [
                        {
                            "content": "What is machine learning?",
                            "role": "user"
                        }
                    ]
                }),
                contentType="application/json"
            )
response_body = json.loads(response["body"].read())
print(f"Invoke Response: {json.dumps(response_body, indent=2)}")
