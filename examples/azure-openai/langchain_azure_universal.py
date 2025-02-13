import os
import dotenv
from dotenv import load_dotenv

from langchain_openai import AzureChatOpenAI
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from langchain.callbacks.base import BaseCallbackHandler
from langchain.callbacks.manager import CallbackManager

#
# 1) Keys and Route Setup
#
print("Initializing environment variables...")
load_dotenv()
azure_openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
javelin_api_key      = os.getenv("JAVELIN_API_KEY")

# The name of your Azure deployment (e.g., "gpt-4") 
# or whatever you’ve set in Azure. 
# Must also match x-javelin-model if Javelin expects that.
model_choice         = "gpt-4"

# Javelin route name, as registered in your javelin route dashboard
route_name           = "azureopenai_univ"

print("Azure OpenAI key:", "FOUND" if azure_openai_api_key else "MISSING")
print("Javelin key:", "FOUND" if javelin_api_key else "MISSING")

#
# 2) Non-Streaming Client
#
llm_non_streaming = AzureChatOpenAI(
    openai_api_key=azure_openai_api_key,
    # Provide your actual API version
    api_version="2024-08-01-preview",
    # The base_url is Javelin’s universal route 
    # pointing to your Azure endpoint:
    base_url="https://api-dev.javelin.live/v1/azureopenai/deployments/gpt-4/",
    validate_base_url=False,
    verbose=True,
    default_headers={
        "x-api-key": javelin_api_key,
        "x-javelin-route": route_name,
        "x-javelin-model": model_choice,
        "x-javelin-provider": "https://javelinpreview.openai.azure.com/openai",
    },
    streaming=False  # Non-streaming
)

#
# 3) Single-Turn Invoke (Non-Streaming)
#
def invoke_non_streaming(question: str) -> str:
    """
    Sends a single user message to the non-streaming LLM
    and returns the text response.
    """
    # Build the messages
    messages = [HumanMessage(content=question)]
    # Use .invoke(...) to get the LLM’s response
    response = llm_non_streaming.invoke(messages)
    # The response is usually an AIMessage. Return its content.
    return response.content

#
# 4) Single-Turn Streaming
#    We'll create a new LLM with streaming=True, plus a callback handler.
#

class StreamCallbackHandler(BaseCallbackHandler):
    """
    Collects tokens as they are streamed, so we can return the final text.
    """
    def __init__(self):
        self.tokens = []

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        self.tokens.append(token)


def invoke_streaming(question: str) -> str:
    """
    Sends a single user message to the LLM (streaming=True).
    Collects the tokens from the callback and returns them as a string.
    """
    callback_handler = StreamCallbackHandler()
    callback_manager = CallbackManager([callback_handler])

    # Create a streaming LLM
    llm_streaming = AzureChatOpenAI(
        openai_api_key=azure_openai_api_key,
        api_version="2024-08-01-preview",
        base_url="https://api-dev.javelin.live/v1/azureopenai/deployments/gpt-4/",
        validate_base_url=False,
        verbose=True,
        default_headers={
            "x-api-key": javelin_api_key,
            "x-javelin-route": route_name,
            "x-javelin-model": model_choice,
            "x-javelin-provider": "https://javelinpreview.openai.azure.com/openai",
        },
        streaming=True,           # <-- streaming on
        callbacks=[callback_handler]  # <-- our custom callback
    )

    messages = [HumanMessage(content=question)]
    response = llm_streaming.invoke(messages)
    # We could check response, but it's usually an AIMessage with partial content
    # The real text is captured in the callback tokens
    return "".join(callback_handler.tokens)

#

def conversation_demo():
    """
    Demonstrates a multi-turn conversation by manually
    appending messages to a list and re-invoking the LLM.
    No memory objects are used, so it’s purely manual.
    """

    conversation_llm = llm_non_streaming

    # Start with a system message 
    messages = [SystemMessage(content="You are a friendly assistant.")]

    user_q1 = "Hello, how are you?"
    messages.append(HumanMessage(content=user_q1))
    response_1 = conversation_llm.invoke(messages)
    messages.append(response_1)  # add AIMessage to context
    print(f"User: {user_q1}\nAssistant: {response_1.content}\n")

    user_q2 = "Can you tell me a fun fact about dolphins?"
    messages.append(HumanMessage(content=user_q2))
    response_2 = conversation_llm.invoke(messages)
    messages.append(response_2)
    print(f"User: {user_q2}\nAssistant: {response_2.content}\n")

    return "Conversation done!"

#
# 6) Main function
#
def main():
    print("=== LangChain AzureOpenAI Example ===")
    
    # 1) Single-turn Non-Streaming Invoke
    print("\n--- Single-turn Non-Streaming Invoke ---")
    question_a = "What is the capital of France?"
    try:
        response_a = invoke_non_streaming(question_a)
        print(f"Question: {question_a}\nAnswer: {response_a}")
    except Exception as e:
        print(f"Error in non-streaming invoke: {e}")
    
    # 2) Single-turn Streaming Invoke
    print("\n--- Single-turn Streaming Invoke ---")
    question_b = "Tell me a quick joke."
    try:
        response_b = invoke_streaming(question_b)
        print(f"Question: {question_b}\nStreamed Answer: {response_b}")
    except Exception as e:
        print(f"Error in streaming invoke: {e}")
    
    # 3) Multi-turn Conversation Demo
    print("\n--- Simple Conversation Demo ---")
    try:
        conversation_demo()
    except Exception as e:
        print(f"Error in conversation demo: {e}")
    
    print("\n=== All done! ===")
    
if __name__ == "__main__":
    main()
