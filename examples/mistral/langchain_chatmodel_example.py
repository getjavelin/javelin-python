import dotenv
import os

dotenv.load_dotenv()

from langchain.chat_models import init_chat_model

model = init_chat_model("mistral-large-latest", model_provider="openai", base_url="https://api-dev.javelin.live/v1",
extra_headers={"x-javelin-route": "mistral_univ", "x-api-key": os.environ.get("JAVELIN_API_KEY"), "Authorization": f"Bearer {os.environ.get('MISTRAL_API_KEY')}"})

print(model.invoke("write a poem about a cat"))