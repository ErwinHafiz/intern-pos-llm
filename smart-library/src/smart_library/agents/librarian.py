from google.adk.agents import LlmAgent

from smart_library.agents import load_prompt
from smart_library.agents.catalog import build_catalog_agent
from smart_library.agents.compare import build_compare_agent
from smart_library.agents.ingest import build_ingest_agent
from smart_library.agents.research import build_research_agent


def build_librarian(backend, model) -> LlmAgent:
    return LlmAgent(
        name="librarian",
        model=model,
        description="Orchestrator Smart Library: mengenali maksud user dan mendelegasikan ke sub-agent.",
        instruction=load_prompt("librarian").replace("<<BACKEND>>", backend.name),
        sub_agents=[
            build_catalog_agent(backend, model),
            build_ingest_agent(backend, model),
            build_research_agent(backend, model),
            build_compare_agent(backend, model),
        ],
    )
