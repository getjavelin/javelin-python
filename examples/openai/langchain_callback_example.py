import dotenv
import os
from typing import Any, Dict, List

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import BaseMessage
from langchain.chat_models import init_chat_model

dotenv.load_dotenv()


class HeaderCallbackHandler(BaseCallbackHandler):
    """Custom callback handler that modifies the headers on chat model start."""

    def __init__(self):
        self.api_key = os.environ.get("JAVELIN_API_KEY")

    def on_chain_start(
        self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any
    ) -> Any:
        """Run when chain starts running."""
        print("Chain started")
        print(serialized, inputs, kwargs)

    def on_chat_model_start(
        self,
        serialized: Dict[str, Any],
        messages: List[List[BaseMessage]],
        **kwargs: Any,
    ) -> Any:
        """Run when Chat Model starts running."""
        # The serialized dict contains the model configuration
        print(self.__super().on_chat_model_start(serialized, messages, **kwargs))
        if "kwargs" in serialized:
            # Add or update the headers in the model kwargs
            if "model_kwargs" not in serialized["kwargs"]:
                serialized["kwargs"]["model_kwargs"] = {}
            if "extra_headers" not in serialized["kwargs"]["model_kwargs"]:
                serialized["kwargs"]["model_kwargs"]["extra_headers"] = {}

            # Determine the route based on the model provider
            provider = serialized.get("name", "").lower()
            route = "azureopenai_univ" if "azure" in provider else "openai_univ"

            headers = {"x-javelin-route": route, "x-api-key": self.api_key}
            serialized["kwargs"]["model_kwargs"]["extra_headers"].update(headers)
            print(f"Modified headers to: {headers}")


# Initialize the callback handler
callback_handler = HeaderCallbackHandler()

# Initialize the chat model with the callback handler
model = init_chat_model(
    "gpt-4o-mini",
    model_provider="openai",
    base_url="http://127.0.0.1:8000/v1",
    extra_headers={
        "x-javelin-route": "openai_univ",
        "x-api-key": os.environ.get("JAVELIN_API_KEY"),
    },
    callbacks=[callback_handler],  # Add our custom callback handler
)

# Test the model
print(model.invoke("Hello, world!"))
