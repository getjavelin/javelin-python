import os
import asyncio
from dotenv import load_dotenv

from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai.types import Content, Part

load_dotenv()

JAVELIN_API_KEY = os.getenv("JAVELIN_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not JAVELIN_API_KEY:
    raise ValueError("Missing JAVELIN_API_KEY in environment")
if not OPENAI_API_KEY:
    raise ValueError("Missing OPENAI_API_KEY in environment")

# Agent 1: Researcher
research_agent = LlmAgent(
    model=LiteLlm(
        model="openai/gpt-4o",
        api_base="https://api-dev.javelin.live/v1",
        extra_headers={
            "x-javelin-route": "openai_univ",
            "x-api-key": JAVELIN_API_KEY,
            "Authorization": f"Bearer {OPENAI_API_KEY}",
        },
    ),
    name="ResearchAgent",
    instruction="Research the query and save findings in state['research'].",
    output_key="research",
)

# Agent 2: Summarizer
summary_agent = LlmAgent(
    model=LiteLlm(
        model="openai/gpt-4o",
        api_base="https://api-dev.javelin.live/v1",
        extra_headers={
            "x-javelin-route": "openai_univ",
            "x-api-key": JAVELIN_API_KEY,
            "Authorization": f"Bearer {OPENAI_API_KEY}",
        },
    ),
    name="SummaryAgent",
    instruction="Summarize state['research'] into state['summary'].",
    output_key="summary",
)

# Agent 3: Reporter
report_agent = LlmAgent(
    model=LiteLlm(
        model="openai/gpt-4o",
        api_base="https://api-dev.javelin.live/v1",
        extra_headers={
            "x-javelin-route": "openai_univ",
            "x-api-key": JAVELIN_API_KEY,
            "Authorization": f"Bearer {OPENAI_API_KEY}",
        },
    ),
    name="ReportAgent",
    instruction="Generate a report from state['summary'] and include a source URL.",
    output_key="report",
)

# Coordinator agent running all three sequentially
coordinator = SequentialAgent(
    name="OpenAI_MultiAgentCoordinator",
    sub_agents=[research_agent, summary_agent, report_agent],
)
root_agent = coordinator


async def main():
    session_service = InMemorySessionService()
    session_service.create_session("openai_multi_agent_app", "user", "sess")

    runner = Runner(
        agent=coordinator,
        app_name="openai_multi_agent_app",
        session_service=session_service,
    )

    # Provide user query
    query = "impact of AI on global education"
    msg = Content(role="user", parts=[Part.from_text(query)])

    final_answer = ""
    async for event in runner.run_async("user", "sess", new_message=msg):
        if event.is_final_response() and event.content:
            final_answer = event.content.parts[0].text
            break

    print("\n--- Final Report ---\n", final_answer)


if __name__ == "__main__":
    asyncio.run(main())
