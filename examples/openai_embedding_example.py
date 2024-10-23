from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os
import dotenv

dotenv.load_dotenv()

# Retrieve environment variables
javelin_api_key = os.getenv('JAVELIN_API_KEY')
llm_api_key = os.getenv("OPENAI_API_KEY")

# Set up local embeddings
embeddings = OpenAIEmbeddings(openai_api_key=llm_api_key)

# Example text to embed
text = "The chemical composition of sugar is C6H12O6."

# Generate embeddings locally
embedding_vector = embeddings.embed_query(text)

print(f"Embedding for '{text}':")
print(f"Vector dimension: {len(embedding_vector)}")
print(f"First 5 values: {embedding_vector[:5]}")

# Example of embedding multiple texts
texts = [
    "The chemical composition of sugar is C6H12O6.",
    "Water has the chemical formula H2O.",
    "Salt is composed of sodium and chloride ions."
]

embedded_texts = embeddings.embed_documents(texts)

print("\nEmbeddings for multiple texts:")
for i, embedding in enumerate(embedded_texts):
    print(f"Text {i+1} - Vector dimension: {len(embedding)}")
    print(f"First 5 values: {embedding[:5]}")
    print()

# Now, let's use Javelin for querying
javelin_headers = {
    "x-api-key": javelin_api_key,      # Javelin API key from admin
    "x-javelin-route": "myusers" # Javelin route to use
}

llm = ChatOpenAI(
    openai_api_base="https://api-dev.javelin.live/v1/query", # Set Javelin's API base URL for query
    openai_api_key=llm_api_key,
    model_kwargs={
        "extra_headers": javelin_headers
    },
)

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant that explains scientific concepts."),
    ("user", "Using the embedding of '{text}', explain the concept in simple terms.")
])

output_parser = StrOutputParser()

chain = prompt | llm | output_parser

# Use the first text as an example for querying
result = chain.invoke({"text": texts[0]})
print("\nJavelin Query Result:")
print(result)
