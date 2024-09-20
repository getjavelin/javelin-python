import os
import pytest
from javelin_sdk import JavelinClient

@pytest.fixture(scope="module")
def javelin_client():
    javelin_api_key = os.getenv("JAVELIN_API_KEY")
    javelin_virtualapikey = os.getenv("JAVELIN_VIRTUALAPIKEY")
    llm_api_key = os.getenv("LLM_API_KEY")

    if not javelin_api_key:
        pytest.skip("JAVELIN_API_KEY environment variable not set")

    client = JavelinClient(
        base_url="https://api-dev.javelin.live",
        javelin_api_key=javelin_api_key,
        javelin_virtualapikey=javelin_virtualapikey,
        llm_api_key=llm_api_key,
    )
    return client
