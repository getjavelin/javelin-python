## Javelin: an Enterprise-Scale, Fast LLM Gateway

[![Upload Python Package](https://github.com/getjavelin/javelin-python/actions/workflows/python-publish.yml/badge.svg?branch=main)](https://github.com/getjavelin/javelin-python/actions/workflows/python-publish.yml)

This is the Python client package for Javelin.

For more information about Javelin, see https://getjavelin.io  
Javelin Documentation: https://docs.getjavelin.io

### Development

For local development, Please change `version = "RELEASE_VERSION"` with any semantic version example : `version = "v0.1.10"` in `pyproject.toml`

*Make sure that the file `pyproject.toml` reverted before commit back to main*

### Installation

```python
  pip install javelin_sdk
```

### Quick Start

```python
from javelin_sdk import (
    JavelinClient,
    JavelinConfig,
    Route,
    NetworkError,
    RouteNotFoundError,
    UnauthorizedError,
)

import os, sys

try:
    javelin_api_key = os.getenv('JAVELIN_API_KEY')
    javelin_virtualapikey = os.getenv('JAVELIN_VIRTUALAPIKEY') #optional
    llm_api_key = os.getenv("OPENAI_API_KEY")

    config = JavelinConfig(
        base_url="https://api-dev.javelin.live",
        javelin_api_key=javelin_api_key,
        javelin_virtualapikey=javelin_virtualapikey, #optional
        llm_api_key=llm_api_key,
    )
    client = JavelinClient(config)

    print('Successfully connected to Javelin Client')

except NetworkError as e:
    print("Failed to create client: Network Error")
    sys.exit()
except UnauthorizedError as e:
    print("Failed to create client: Unauthorized")
    sys.exit()

# Create a route object
route_data = {
    "name": "test_route_1",
    "type": "chat",
    "models": [
        {
            "name": "gpt-3.5-turbo",
            "enabled": True,
            "provider": "openai",
            "suffix": "/v1/chat/completions",
        }
    ],
    "config": {
        "archive": True,
        "organization": "myusers",
        "retries": 3,
        "rate_limit": 7,
    },
}

route = Route.parse_obj(route_data)
try:
    client.create_route(route)
except NetworkError as e:
    print("Failed to create route: Network Error")

query_data = {
    "model": "gpt-3.5-turbo",
    "messages": [
        {"role": "system", "content": "You are a helpful assistant that translates English to French."},
        {"role": "user", "content": "AI has the power to transform humanity and make the world a better place"},
    ],
    "temperature": 0.8,
}

# query the llm
try:
    response = client.query_route("test_route_1", query_data)
except RouteNotFoundError as e:
    print("Route Not Found")

```
