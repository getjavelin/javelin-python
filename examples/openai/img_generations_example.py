import base64
from openai import OpenAI
from javelin_sdk import JavelinClient, JavelinConfig
import os
import dotenv

dotenv.load_dotenv()

# Load API keys from environment variables
JAVELIN_API_KEY = os.getenv("JAVELIN_API_KEY")
LLM_API_KEY = os.getenv("LLM_API_KEY")
BASE_URL = os.getenv("BASE_URL")

# Configure Javelin
config = JavelinConfig(
    base_url=BASE_URL,
    javelin_api_key=JAVELIN_API_KEY,
    llm_api_key=LLM_API_KEY,
)
javelin_client = JavelinClient(config)

client = OpenAI(api_key=LLM_API_KEY)
route_name = "openai_univ"  # define your universal route name here
javelin_client.register_openai(client, route_name=route_name)

# --- Example 1: Edit an image ---
# result = client.images.edit(
#     model="gpt-image-1",
#     image=open("examples/dog.png", "rb"),
#     prompt="an angry dog"
# )
# image_base64 = result.data[0].b64_json
# image_bytes = base64.b64decode(image_base64)
# with open("angry_dog_2.png", "wb") as f:
#     f.write(image_bytes)

# --- Example 2: Create image variations ---
# response = client.images.create_variation(
#     image=open("examples/dog.png", "rb"),
#     n=2,
#     size="1024x1024"
# )
# for idx, img_data in enumerate(response.data):
#     image_bytes = base64.b64decode(img_data.b64_json)
#     with open(f"dog_variation_{idx+1}.png", "wb") as f:
#         f.write(image_bytes)

# --- Example 3: Generate an image ---
img = client.images.generate(
    model="gpt-image-1",
    prompt="A friendly dog playing in a park.",
    n=1,
    size="1024x1024",
)

image_bytes = base64.b64decode(img.data[0].b64_json)
with open("generated_image.png", "wb") as f:
    f.write(image_bytes)
