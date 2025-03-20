import dotenv
import os

dotenv.load_dotenv()

from langchain_openai import AzureChatOpenAI

model = AzureChatOpenAI(
    azure_endpoint="https://api-dev.javelin.live/v1",
    azure_deployment="gpt35",
    openai_api_version="2023-03-15-preview",
    extra_headers={"x-javelin-route": "azureopenai_univ", "x-api-key": os.environ.get("JAVELIN_API_KEY")}
)

print(model.invoke("Hello, world!"))