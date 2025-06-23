[![Ask DeepWiki](https://deepwiki.com/badge.svg "DeepWiki Documentation")](https://deepwiki.com/getjavelin/javelin-python)

## Javelin: an Enterprise-Scale, Fast LLM Gateway/Edge

This is the Python client package for Javelin.

For more information about Javelin, see https://getjavelin.com

Javelin Documentation: https://docs.getjavelin.io

### Development

For local development, Please change `version = "RELEASE_VERSION"` with any semantic version example : `version = "v0.1.10"` in `pyproject.toml`

*Make sure that the file `pyproject.toml` reverted before commit back to main*

### Installation

```python
  pip install javelin-sdk
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
pip uninstall javelin-sdk -y

# Build the package
poetry build

# Install the newly built package
pip install dist/javelin_sdk-<version>-py3-none-any.whl
```

## [Universal Endpoints](https://docs.getjavelin.io/docs/javelin-core/integration#unified-endpoints)

Javelin provides universal endpoints that allow you to use a consistent interface across different LLM providers. Here are the main patterns:

#### Azure OpenAI
- [Basic Azure OpenAI integration](https://github.com/getjavelin/javelin-python/blob/main/examples/azure-openai/azure-universal.py)
- [Universal endpoint implementation](https://github.com/getjavelin/javelin-python/blob/main/examples/azure-openai/javelin_azureopenai_univ_endpoint.py)
- [OpenAI-compatible interface](https://github.com/getjavelin/javelin-python/blob/main/examples/azure-openai/openai_compatible_univ_azure.py)

#### Bedrock
- [Basic Bedrock integration](https://github.com/getjavelin/javelin-python/blob/main/examples/bedrock/bedrock_client_universal.py)
- [Universal endpoint implementation](https://github.com/getjavelin/javelin-python/blob/main/examples/bedrock/javelin_bedrock_univ_endpoint.py)
- [OpenAI-compatible interface](https://github.com/getjavelin/javelin-python/blob/main/examples/bedrock/openai_compatible_univ_bedrock.py)

#### Gemini
- [Basic Gemini integration](https://github.com/getjavelin/javelin-python/blob/main/examples/gemini/gemini-universal.py)
- [Universal endpoint implementation](https://github.com/getjavelin/javelin-python/blob/main/examples/gemini/javelin_gemini_univ_endpoint.py)
- [OpenAI-compatible interface](https://github.com/getjavelin/javelin-python/blob/main/examples/gemini/openai_compatible_univ_gemini.py)

### Agent Examples
- [CrewAI integration](https://github.com/getjavelin/javelin-python/blob/main/examples/agents/crewai_javelin.ipynb)
- [LangGraph integration](https://github.com/getjavelin/javelin-python/blob/main/examples/agents/langgraph_javelin.ipynb)

### Basic Examples
- [Asynchronous example](https://github.com/getjavelin/javelin-python/blob/main/examples/route_examples/aexample.py)
- [Synchronous example](https://github.com/getjavelin/javelin-python/blob/main/examples/route_examples/example.py)
- [Drop-in replacement example](https://github.com/getjavelin/javelin-python/blob/main/examples/route_examples/drop_in_replacement.py)

### Advanced Examples
- [Document processing](https://github.com/getjavelin/javelin-python/blob/main/examples/gemini/document_processing.py)
- [RAG implementation](https://github.com/getjavelin/javelin-python/blob/main/examples/rag/javelin_rag_embeddings_demo.ipynb)

## Additional Integration Patterns

For more detailed examples and integration patterns, check out:

- [Azure OpenAI Integration](https://docs.getjavelin.io/docs/javelin-core/integration#2-azure-openai-api-endpoints)
- [AWS Bedrock Integration](https://docs.getjavelin.io/docs/javelin-core/integration#3-aws-bedrock-api-endpoints)
- [Supported Language Models](https://docs.getjavelin.io/docs/javelin-core/supported-llms)
