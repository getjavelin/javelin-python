## Javelin: an Enterprise-Scale, Fast LLM Gateway

[![Upload Python Package](https://github.com/getjavelin/javelin-python/actions/workflows/python-publish.yml/badge.svg?branch=main)](https://github.com/getjavelin/javelin-python/actions/workflows/python-publish.yml)

This is the Python client package for Javelin.

For more information about Javelin, see https://getjavelin.io  
Javelin Documentation: https://docs.getjavelin.io

### Installation

```python
  pip install javelin_sdk
```

### Quick Start

```python
  from javelin_sdk import (
    JavelinClient,
    Route,
    NetworkError,
    RouteNotFoundError,
    UnauthorizedError,
  )

  import os, sys

  try:
       javelin_api_key = os.getenv('JAVELIN_API_KEY')
       llm_api_key = os.getenv("OPENAI_API_KEY")

       client = JavelinClient(base_url="https://api-dev.javelin.live", # Set Javelin's API base URL for query
                              javelin_api_key=javelin_api_key,
                              llm_api_key=llm_api_key)

       print('sucessfully connected to Javelin Client')

  except NetworkError as e:
       print("Failed to create client: Network Error")
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

### System Architecture

```mermaid
graph TB
    User((User))
    ExternalLLM[("External LLM API<br/>(e.g., OpenAI)")]
    ExternalLLM:::external

    subgraph "Javelin SDK"
        JavelinClient["Javelin Client<br/>(Python)"]
        JavelinClient:::main

        subgraph "Core Components"
            Models["Models<br/>(Pydantic)"]
            Exceptions["Exceptions"]
            HTTPClient["HTTP Client<br/>(httpx)"]
        end

        subgraph "API Handlers"
            GatewayHandler["Gateway Handler"]
            ProviderHandler["Provider Handler"]
            RouteHandler["Route Handler"]
            SecretHandler["Secret Handler"]
            TemplateHandler["Template Handler"]
            QueryHandler["Query Handler"]
        end
    end

    subgraph "Javelin CLI"
        CLIMain["CLI Main"]
        CLICommands["CLI Commands"]
    end

    subgraph "External Services"
        JavelinAPI["Javelin API"]
        JavelinAPI:::external
    end

    User --> CLIMain
    User --> JavelinClient
    CLIMain --> CLICommands
    CLICommands --> JavelinClient
    JavelinClient --> Models
    JavelinClient --> Exceptions
    JavelinClient --> HTTPClient
    JavelinClient --> GatewayHandler
    JavelinClient --> ProviderHandler
    JavelinClient --> RouteHandler
    JavelinClient --> SecretHandler
    JavelinClient --> TemplateHandler
    JavelinClient --> QueryHandler
    HTTPClient --> JavelinAPI
    QueryHandler --> ExternalLLM

    classDef main fill:#1168bd,stroke:#0b4884,color:#ffffff
    classDef component fill:#4682b4,stroke:#315b7e,color:#ffffff
    classDef external fill:#999999,stroke:#666666,color:#ffffff

    class JavelinClient main
    class Models,Exceptions,HTTPClient,GatewayHandler,ProviderHandler,RouteHandler,SecretHandler,TemplateHandler,QueryHandler,CLIMain,CLICommands component
    class JavelinAPI,ExternalLLM external
```
