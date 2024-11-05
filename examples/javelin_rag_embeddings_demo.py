import os

import bs4
import dotenv
from langchain import hub
from langchain_chroma import Chroma
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import AzureChatOpenAI, ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

dotenv.load_dotenv()

javelin_api_key = os.getenv("JAVELIN_API_KEY")
llm_api_key = os.getenv("JAVELIN_AZURE_OPENAI_API_KEY")

javelin_headers = {"x-api-key": javelin_api_key, "x-javelin-route": "azureopenai"}

llm = AzureChatOpenAI(
    api_key=llm_api_key,
    azure_endpoint="https://api-dev.javelin.live/v1/query/azureopenai",
    azure_deployment="gpt35",
    openai_api_version="2024-02-15-preview",
    model_kwargs={"extra_headers": javelin_headers}
)

loader = WebBaseLoader(
    web_paths=("https://lilianweng.github.io/posts/2023-06-23-agent/",),
    bs_kwargs=dict(
        parse_only=bs4.SoupStrainer(
            class_=("post-content", "post-title", "post-header")
        )
    ),
)
docs = loader.load()

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
splits = text_splitter.split_documents(docs)
vectorstore = Chroma.from_documents(documents=splits, embedding=OpenAIEmbeddings())

retriever = vectorstore.as_retriever()
prompt = hub.pull("rlm/rag-prompt")


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

from openai import OpenAI, AzureOpenAI

client = OpenAI()

javelin_api_key = os.getenv("JAVELIN_API_KEY")
llm_api_key = os.getenv("OPENAI_API_KEY")

javelin_headers_embedding = {
    "x-api-key": javelin_api_key,
    "x-javelin-route": "openaiembedding"
}

client_embedding = OpenAI(
    api_key=llm_api_key,
    base_url="https://api-dev.javelin.live/v1/query",
    default_headers=javelin_headers_embedding,
)

embedding_response = client_embedding.embeddings.create(
    input="Your text string goes here",
    model="text-embedding-3-small"
)

print(embedding_response.data[0].embedding)

llm_api_key = os.environ["JAVELIN_AZURE_OPENAI_API_KEY"]

javelin_headers = {
    "x-api-key": javelin_api_key,
    "x-javelin-route": "azureopenaiembeddings",
}

azure_openai_client = AzureOpenAI(
    api_key=llm_api_key,
    base_url="https://api-dev.javelin.live/v1/query",
    default_headers=javelin_headers,
    api_version="2023-05-15",
)

azure_openai_response = azure_openai_client.embeddings.create(
    input="Your text string goes here",
    model="text-embedding-3-small"
)

print(azure_openai_response.data[0].embedding)

print(rag_chain.invoke("What is Task Decomposition?"))
