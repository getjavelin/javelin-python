import os
from openai import AzureOpenAI
from javelin_sdk import JavelinClient, JavelinConfig
from dotenv import load_dotenv

load_dotenv()

def initialize_client():
    """
    Creates the AzureOpenAI client and registers it with Javelin.
    Returns the AzureOpenAI client object if successful, else None.
    """
    javelin_api_key = os.getenv("JAVELIN_API_KEY") # add your javelin api key here
    azure_openai_api_key = os.getenv("AZURE_OPENAI_API_KEY") # Add your Azure OpenAI key

    if not javelin_api_key:
        print("Error: JAVELIN_API_KEY is not set!")
        return None
    else:
        print("JAVELIN_API_KEY found.")

    if not azure_openai_api_key:
        print("Warning: AZURE_OPENAI_API_KEY is not set!")
    else:
        print("AZURE_OPENAI_API_KEY found.")

    # Create the Azure client
    azure_client = AzureOpenAI(
        # Typically "2023-07-01-preview" or a more recent version
        api_version="2023-07-01-preview",
        azure_endpoint="https://javelinpreview.openai.azure.com",
        api_key=azure_openai_api_key
    )

    # Initialize the Javelin client and register the Azure client
    config = JavelinConfig(javelin_api_key=javelin_api_key)
    javelin_client = JavelinClient(config)
    rout_name = "azureopenai_univ" # Define the unversal route name
    javelin_client.register_azureopenai(azure_client, route_name=rout_name)

    return azure_client


def get_chat_completion_sync(azure_client, messages):
    """
    Calls the Azure Chat Completions endpoint (non-streaming).
    Takes a list of message dicts, returns JSON response as a string.
    Example model: 'gpt-4' or your deployed name (like 'gpt-4o').
    """

    response = azure_client.chat.completions.create(
        model="gpt-4",  # Adjust to your Azure deployment name
        messages=messages
    )
    return response.to_json()


def get_chat_completion_stream(azure_client, messages):
    """
    Calls the Azure Chat Completions endpoint with streaming=True.
    Returns the concatenated text from the streamed chunks.
    """
    response = azure_client.chat.completions.create(
        model="gpt-4",  # Adjust to your Azure deployment name
        messages=messages,
        stream=True
    )

    # Accumulate streamed text
    streamed_text = []
    for chunk in response:
        if hasattr(chunk, "choices") and chunk.choices:
            delta = chunk.choices[0].delta
            if delta is not None:
                # Use getattr to safely retrieve the 'content' attribute
                content = getattr(delta, "content", "")
                if content:
                    streamed_text.append(content)
    return "".join(streamed_text)



def get_text_completion(azure_client, prompt):
    """
    Demonstrates Azure text completion (non-chat).
    For this, your Azure resource must have a 'completions' model deployed,
    e.g. 'text-davinci-003'.
    """
    response = azure_client.completions.create(
        model="gpt-4o",  # Adjust to your actual Azure completions model name
        prompt=prompt,
        max_tokens=50,
        temperature=0.7
    )
    return response.to_json()


def get_embeddings(azure_client, text):
    """
    Demonstrates Azure embeddings endpoint.
    Your Azure resource must have an embeddings model, e.g. 'text-embedding-ada-002'.
    """
    response = azure_client.embeddings.create(
        model="text-embedding-ada-002",  # Adjust to your embeddings model name
        input=text
    )
    return response.to_json()


def main():
    print("Azure OpenAI via Javelin Testing:")
    azure_client = initialize_client()
    if azure_client is None:
        print("Client initialization failed.")
        return

    # Example chat messages
    messages = [
        {"role": "user", "content": "say hello"}
    ]

    # 1) Chat Completion (Synchronous)
    try:
        print("\n--- Chat Completion (Non-Streaming) ---")
        response_chat_sync = get_chat_completion_sync(azure_client, messages)
        if not response_chat_sync.strip():
            print("Error: Empty response  failed")
        else:
            print("Response:\n", response_chat_sync)
    except Exception as e:
        print("Error in chat completion (sync):", e)

    # 2) Chat Completion (Streaming)
    try:
        print("\n--- Chat Completion (Streaming) ---")
        response_streamed = get_chat_completion_stream(azure_client, messages)
        if not response_streamed.strip():
            print("Error: Empty response  failed")
        else:
            print("Response:\n", response_streamed)
    except Exception as e:
        print("Error in chat completion (streaming):", e)

    # 3) Embeddings
    try:
        print("\n--- Embeddings ---")
        embed_text = "Sample text to embed."
        embed_resp = get_embeddings(azure_client, embed_text)
        if not embed_resp.strip():
            print("Error: Empty response  failed")
        else:
            print("Response:\n", embed_resp)
    except Exception as e:
        print("Error in embeddings:", e)

    print("\nScript complete.")


if __name__ == "__main__":
    main()
