import json
import os

from dotenv import load_dotenv
from langchain.callbacks.manager import CallbackManager
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

# LLM classes from langchain_openai
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

load_dotenv()

# -----------------------------------------------------------------------------
# 1) Configuration
# -----------------------------------------------------------------------------
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")  # add your openai api key here
JAVELIN_API_KEY = os.environ.get("JAVELIN_API_KEY")  # add your javelin api key here
MODEL_NAME_CHAT = "gpt-3.5-turbo"  # For chat
MODEL_NAME_EMBED = "text-embedding-ada-002"
ROUTE_NAME = "openai_univ"
BASE_URL = os.getenv("JAVELIN_BASE_URL", "https://api.javelin.live")  # Default base URL


def init_chat_llm_non_streaming():
    """
    Returns a non-streaming ChatOpenAI instance (for synchronous chat).
    """
    return ChatOpenAI(
        openai_api_key=OPENAI_API_KEY,
        openai_api_base=f"{BASE_URL}/v1/openai",
        default_headers={
            "x-api-key": JAVELIN_API_KEY,
            "x-javelin-route": ROUTE_NAME,
            "x-javelin-provider": "https://api.openai.com/v1",
            "x-javelin-model": MODEL_NAME_CHAT,
        },
        streaming=False,
    )


def init_chat_llm_streaming():
    """
    Returns a streaming ChatOpenAI instance (for streaming chat).
    """
    return ChatOpenAI(
        openai_api_key=OPENAI_API_KEY,
        openai_api_base=f"{BASE_URL}/v1/openai",
        default_headers={
            "x-api-key": JAVELIN_API_KEY,
            "x-javelin-route": ROUTE_NAME,
            "x-javelin-provider": "https://api.openai.com/v1",
            "x-javelin-model": MODEL_NAME_CHAT,
        },
        streaming=True,
    )


def init_embeddings_llm():
    """
    Returns an OpenAIEmbeddings instance for embeddings (e.g., text-embedding-ada-002).
    """
    return OpenAIEmbeddings(
        openai_api_key=OPENAI_API_KEY,
        openai_api_base=f"{BASE_URL}/v1/openai",
        default_headers={
            "x-api-key": JAVELIN_API_KEY,
            "x-javelin-route": ROUTE_NAME,
            "x-javelin-provider": "https://api.openai.com/v1",
            "x-javelin-model": MODEL_NAME_EMBED,
        },
    )


# -----------------------------------------------------------------------------
# 2) Chat Completion (Synchronous)
# -----------------------------------------------------------------------------
def chat_completion_sync(question: str) -> str:
    """
    Single-turn chat, non-streaming. Returns the final text.
    """
    llm = init_chat_llm_non_streaming()

    prompt = ChatPromptTemplate.from_messages(
        [("system", "You are a helpful assistant."), ("user", "{input}")]
    )
    parser = StrOutputParser()
    chain = prompt | llm | parser

    return chain.invoke({"input": question})


# -----------------------------------------------------------------------------
# 3) Chat Completion (Streaming)
# -----------------------------------------------------------------------------
class StreamCallbackHandler(BaseCallbackHandler):
    def __init__(self):
        self.tokens = []

    def on_llm_new_token(self, token: str, **kwargs):
        self.tokens.append(token)

    # Prevent argument errors in some versions:
    def on_chat_model_start(self, serialized, messages, **kwargs):
        pass


def chat_completion_stream(question: str) -> str:
    """
    Single-turn chat, streaming. Returns the combined partial tokens.
    """
    llm = init_chat_llm_streaming()
    callback_handler = StreamCallbackHandler()
    CallbackManager([callback_handler])
    # In some versions, you might pass callbacks to llm
    llm.callbacks = [callback_handler]

    prompt = ChatPromptTemplate.from_messages(
        [("system", "You are a helpful assistant."), ("user", "{input}")]
    )
    parser = StrOutputParser()
    streaming_chain = prompt | llm | parser

    streaming_chain.invoke({"input": question})
    return "".join(callback_handler.tokens)


# -----------------------------------------------------------------------------
# 4) Embeddings Example
# -----------------------------------------------------------------------------
def get_embeddings(text: str) -> str:
    """
    Example generating embeddings from text-embedding-ada-002.
    Returns a string representation of the vector.
    """
    emb = init_embeddings_llm()
    # We'll embed a single query
    vector = emb.embed_query(text)
    return json.dumps(vector)


# -----------------------------------------------------------------------------
# 5) Conversation Demo (Manual, Non-Streaming)
# -----------------------------------------------------------------------------
def conversation_demo() -> None:
    """
    Multi-turn chat by manually rebuilding the prompt each turn.
    """
    llm = init_chat_llm_non_streaming()
    parser = StrOutputParser()

    # Start with a list of messages
    messages = [("system", "You are a friendly assistant.")]

    # 1) Turn 1
    user_q1 = "Hello, how are you?"
    messages.append(("user", user_q1))

    prompt_1 = ChatPromptTemplate.from_messages(messages)
    chain_1 = prompt_1 | llm | parser
    ans1 = chain_1.invoke({})
    messages.append(("assistant", ans1))
    print(f"User: {user_q1}\nAssistant: {ans1}\n")

    # 2) Turn 2
    user_q2 = "Can you tell me a fun fact about dolphins?"
    messages.append(("user", user_q2))

    prompt_2 = ChatPromptTemplate.from_messages(messages)
    chain_2 = prompt_2 | llm | parser
    ans2 = chain_2.invoke({})
    messages.append(("assistant", ans2))
    print(f"User: {user_q2}\nAssistant: {ans2}\n")


# -----------------------------------------------------------------------------
# 6) Main
# -----------------------------------------------------------------------------
def main():
    print("=== LangChain + OpenAI Javelin Examples (No Text Completion) ===")

    # 1) Chat Completion (Synchronous)
    print("\n--- Chat Completion: Synchronous ---")
    try:
        question = "What is machine learning?"
        result = chat_completion_sync(question)
        if not result.strip():
            print("Error: Empty response  failed")
        else:
            print(f"Prompt: {question}\nAnswer:\n{result}")
    except Exception as e:
        print(f"Error in synchronous chat completion: {e}")

    # 2) Chat Completion (Streaming)
    print("\n--- Chat Completion: Streaming ---")
    try:
        question2 = "Tell me a short joke."
        result_stream = chat_completion_stream(question2)
        if not result_stream.strip():
            print("Error: Empty response  failed")
        else:
            print(f"Prompt: {question2}\nStreamed Answer:\n{result_stream}")
    except Exception as e:
        print(f"Error in streaming chat completion: {e}")

    # 3) Embeddings Example
    print("\n--- Embeddings Example ---")
    try:
        sample_text = "The quick brown fox jumps over the lazy dog."
        embed_vec = get_embeddings(sample_text)
        if not embed_vec.strip():
            print("Error: Empty response  failed")
        else:
            print(f"Text: {sample_text}\nEmbedding Vector:\n{embed_vec[:100]} ...")
    except Exception as e:
        print(f"Error in embeddings: {e}")

    # 4) Conversation Demo (Manual, Non-Streaming)
    print("\n--- Conversation Demo (Manual, Non-Streaming) ---")
    try:
        conversation_demo()
    except Exception as e:
        print(f"Error in conversation demo: {e}")

    print("\n=== Script Complete ===")


if __name__ == "__main__":
    main()
