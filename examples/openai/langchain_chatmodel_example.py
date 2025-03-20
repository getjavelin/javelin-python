import dotenv
import os

dotenv.load_dotenv()

from langchain.chat_models import init_chat_model

model = init_chat_model("gpt-4o-mini", model_provider="openai", base_url="https://api-dev.javelin.live/v1",
extra_headers={"x-javelin-route": "openai_univ", "x-api-key": os.environ.get("JAVELIN_API_KEY")})

print(model.invoke("Hello, world!"))