import os
import asyncio

# OpenAI Agents SDK imports
from agents import (
    Agent,
    Runner,
    set_default_openai_api,
    set_default_openai_client,
    ModelSettings,
)

from openai import AsyncOpenAI
from javelin_sdk import JavelinClient, JavelinConfig
from dotenv import load_dotenv

##############################################################################
# 1) Environment & Basic Setup
##############################################################################
load_dotenv()

# Use Chat Completions endpoint instead of /v1/responses
set_default_openai_api("chat_completions")

openai_api_key = os.getenv("OPENAI_API_KEY", "")
javelin_api_key = os.getenv("JAVELIN_API_KEY", "")
javelin_base_url = os.getenv("JAVELIN_BASE_URL", "")

if not (openai_api_key and javelin_api_key and javelin_base_url):
    raise ValueError("Missing OPENAI_API_KEY, JAVELIN_API_KEY, or JAVELIN_BASE_URL in .env")

# Create async OpenAI client
async_openai_client = AsyncOpenAI(api_key=openai_api_key)

# Register with Javelin
javelin_client = JavelinClient(JavelinConfig(
    javelin_api_key=javelin_api_key,
    base_url=javelin_base_url
))
javelin_client.register_openai(async_openai_client, route_name="openai_univ")  # Adjust route name if needed

# Let the Agents SDK use this Javelin-patched client globally
set_default_openai_client(async_openai_client)

##############################################################################
# 2) Child Agent A: "Faux Search" (actually just an LLM summary)
##############################################################################
faux_search_agent = Agent(
    name="FauxSearchAgent",
    instructions=(
        "You pretend to search the web for the user's topic. "
        "In reality, you only use your internal knowledge to produce a short summary. "
        "Focus on being concise and factual in describing the topic."
    ),
)

##############################################################################
# 3) Child Agent B: Translator (English → Spanish)
##############################################################################
translator_agent = Agent(
    name="TranslatorAgent",
    instructions="Translate any English text into Spanish. Keep it concise."
)

##############################################################################
# 4) Orchestrator Agent: Must call faux_search, then translator
##############################################################################
orchestrator_agent = Agent(
    name="OrchestratorAgent",
    instructions=(
        "You MUST do these steps:\n"
        "1) Call 'faux_search_agent' to produce a short summary.\n"
        "2) Pass that summary to 'translator_agent' to translate it into Spanish.\n"
        "Return only the Spanish text.\n"
        "Do not skip or respond directly yourself!"
    ),
    model_settings=ModelSettings(tool_choice="required"),  # Forcing tool usage
    tools=[
        faux_search_agent.as_tool(
            tool_name="summarize_topic",
            tool_description="Produce a concise internal summary of the user’s topic."
        ),
        translator_agent.as_tool(
            tool_name="translate_to_spanish",
            tool_description="Translate text into Spanish."
        ),
    ],
)

##############################################################################
# 5) Demo Usage
##############################################################################
async def main():
    user_query = "Why is pollution increasing ?"
    print(f"\n=== User Query: {user_query} ===\n")

    final_result = await Runner.run(orchestrator_agent, user_query)
    print("=== Final Output ===\n")
    print(final_result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
