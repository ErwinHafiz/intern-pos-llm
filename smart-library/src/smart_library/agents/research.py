from google.adk.agents import LlmAgent

from smart_library.agents import load_prompt
from smart_library.tools.catalog_tools import make_catalog_tools
from smart_library.tools.research_tools import make_research_tools


def build_research_agent(backend, model) -> LlmAgent:
    set_scope = make_catalog_tools(backend)[2]
    # mode="chat": menerima transfer dan bisa diskusi multi-turn dengan user
    return LlmAgent(
        name="research_agent",
        mode="chat",
        model=model,
        description="Mencari, menjawab pertanyaan, meringkas, dan membahas isi dokumen dengan kutipan sumber.",
        instruction=load_prompt("research"),
        tools=[*make_research_tools(backend), set_scope],
    )
