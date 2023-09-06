## Javelin: an Enterprise-Scale, Fast LLM Gateway 

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

  # create a route
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
