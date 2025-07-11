import base64
import os

from openai import OpenAI

from javelin_sdk import JavelinClient, JavelinConfig

# Environment Variables
openai_api_key = os.getenv("OPENAI_API_KEY")
javelin_api_key = os.getenv("JAVELIN_API_KEY")
gemini_api_key = os.getenv("GEMINI_API_KEY")

# Initialize Javelin Client
config = JavelinConfig(
    javelin_api_key=javelin_api_key,
)
client = JavelinClient(config)


# Initialize Javelin Client
def initialize_javelin_client():
    javelin_api_key = os.getenv("JAVELIN_API_KEY")
    config = JavelinConfig(
        javelin_api_key=javelin_api_key, base_url=os.getenv("JAVELIN_BASE_URL")
    )
    return JavelinClient(config)


# Create Gemini client
def create_gemini_client():
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    return OpenAI(
        api_key=gemini_api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )


# Register Gemini client with Javelin
def register_gemini(client, openai_client):
    client.register_gemini(openai_client, route_name="openai")


# Gemini Chat Completions
def gemini_chat_completions(openai_client):
    # Read the PDF file in binary mode (Download from
    # https://github.com/run-llama/llama_index/blob/main/docs/docs/examples/data/10k/lyft_2021.pdf)
    with open("lyft_2021.pdf", "rb") as pdf_file:
        file_data = base64.b64encode(pdf_file.read()).decode("utf-8")

    response = openai_client.chat.completions.create(
        model="gemini-2.0-flash-001",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What's the net income for 2021?"},
                    {
                        "type": "file",
                        "data": file_data,  # Base64-encoded data
                        "mimeType": "application/pdf",
                    },
                ],
            }
        ],
    )
    print(response.model_dump_json(indent=2))


def main_sync():
    client = initialize_javelin_client()
    openai_client = create_gemini_client()
    register_gemini(client, openai_client)
    gemini_chat_completions(openai_client)


def main():
    main_sync()  # Run synchronous calls


if __name__ == "__main__":
    main()
