from langchain_openai import AzureChatOpenAI
import dotenv
import os

dotenv.load_dotenv()

url = os.path.join(os.getenv("JAVELIN_BASE_URL"), "v1")
print(url)
model = AzureChatOpenAI(
    azure_endpoint=url,
    azure_deployment="gpt35",
    openai_api_version="2023-03-15-preview",
    extra_headers={
        "x-javelin-route": "azureopenai_univ",
        "x-api-key": os.environ.get("JAVELIN_API_KEY"),
    },
)

print(model.invoke("Hello, world!"))
