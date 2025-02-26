from google import genai
import os
import dotenv

dotenv.load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

response = client.models.generate_content_stream(
    model="gemini-2.0-flash", contents=["Explain how AI works"]
)
for chunk in response:
    print(chunk)
    print(chunk.text, end="")
