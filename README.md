## Javelin: an Enterprise-Scale, Fast LLM Gateway/Edge

This is the Python client package for Javelin.

For more information about Javelin, see https://getjavelin.com
Javelin Documentation: https://docs.getjavelin.io

### Development

For local development, Please change `version = "RELEASE_VERSION"` with any semantic version example : `version = "v0.1.10"` in `pyproject.toml`

*Make sure that the file `pyproject.toml` reverted before commit back to main*

### Installation

```python
  pip install javelin_sdk
```

### Quick Start Guide

## Development Setup

### Setting up Virtual Environment

#### Windows

```batch
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install poetry
poetry install
```

#### macOS/Linux

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install poetry
poetry install
```

### Building and Installing the SDK

```bash
# Uninstall any existing version
pip uninstall javelin_sdk -y

# Build the package
poetry build

# Install the newly built package
pip install dist/javelin_sdk-<version>-py3-none-any.whl
```

### Direct OpenAI-Compatible Usage

```python
from openai import OpenAI

# Initialize client with Javelin endpoint
client = OpenAI(
    base_url="https://api.javelin.live/v1/query/your_route",
    api_key="your_api_key"
)

# Make requests using standard OpenAI format
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
    ]
)
```

### Using Javelin SDK

```python
import os
from openai import OpenAI
import dotenv
dotenv.load_dotenv()
# Configure regular route with Javelin headers
javelin_api_key = os.getenv("JAVELIN_API_KEY")
llm_api_key = os.getenv("OPENAI_API_KEY")
javelin_headers = {
    "x-api-key": javelin_api_key,
}

client = OpenAI(
    base_url="https://api-dev.javelin.live/v1/query/<route>",
    default_headers=javelin_headers
)

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "user", "content": "hello"}
    ],
)

print(response.model_dump_json(indent=2))
```

### Using Universal Endpoints in OpenAI-Compatible Format

```python
from javelin_sdk import JavelinClient, JavelinConfig

# Setup client configuration
config = JavelinConfig(
    base_url="https://api.javelin.live",
    javelin_api_key="your_javelin_api_key"
)

client = JavelinClient(config)

# Set headers for universal endpoint
custom_headers = {
    "Content-Type": "application/json",
    "x-javelin-route": "univ_bedrock"  # Change route as needed (univ_azure, univ_bedrock, univ_gemini)
}
client.set_headers(custom_headers)

# Make requests using OpenAI format
response = client.chat.completions.create(
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What are the three primary colors?"}
    ],
    temperature=0.7,
    max_tokens=150,
    model="amazon.titan-text-express-v1"  # Use appropriate model for your endpoint
)
```

## Additional Integration Patterns

For more detailed examples and integration patterns, check out:

- [Azure OpenAI Integration](https://docs.getjavelin.io/docs/javelin-core/integration#2-azure-openai-api-endpoints)
- [AWS Bedrock Integration](https://docs.getjavelin.io/docs/javelin-core/integration#2-azure-openai-api-endpoints)
- [Supported Language Models](https://docs.getjavelin.io/docs/javelin-core/supported-llms)

## [Universal Endpoints](https://docs.getjavelin.io/docs/javelin-core/integration#unified-endpoints)

Javelin provides universal endpoints that allow you to use a consistent interface across different LLM providers. Here are the main patterns:

#### Azure OpenAI
- [Basic Azure OpenAI integration](examples/azure-openai/azure-universal.py)
- [Universal endpoint implementation](examples/azure-openai/javelin_azureopenai_univ_endpoint.py)
- [OpenAI-compatible interface](examples/azure-openai/openai_compatible_univ_azure.py)

#### Bedrock
- [Basic Bedrock integration](examples/bedrock/bedrock_client_universal.py)
- [Universal endpoint implementation](examples/bedrock/javelin_bedrock_univ_endpoint.py)
- [OpenAI-compatible interface](examples/bedrock/openai_compatible_univ_bedrock.py)

#### Gemini
- [Basic Gemini integration](examples/gemini/gemini-universal.py)
- [Universal endpoint implementation](examples/gemini/javelin_gemini_univ_endpoint.py)
- [OpenAI-compatible interface](examples/gemini/openai_compatible_univ_gemini.py)


### Agent Examples
- [CrewAI integration](examples/agents/crewai_javelin.ipynb)
- [LangGraph integration](examples/agents/langgraph_javelin.ipynb)

### Basic Examples
- [Asynchronous example](examples/route_examples/aexample.py)
- [Synchronous example](examples/route_examples/example.py)
- [Drop-in replacement example](examples/route_examples/drop_in_replacement.py)

### Advanced Examples
- [Document processing](examples/gemini/document_processing.py)
- [RAG implementation](examples/rag/javelin_rag_embeddings_demo.ipynb)
