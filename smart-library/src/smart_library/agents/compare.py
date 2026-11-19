from google.adk.agents import LlmAgent

from smart_library.agents import load_prompt
from smart_library.workflows.compare_pipeline import make_compare_pipeline


def build_compare_agent(backend, model) -> LlmAgent:
    return LlmAgent(
        name="compare_agent",
        mode="task",
        model=model,
        description="Membandingkan 2+ target (dataset dan/atau dokumen, kombinasi apa pun) dalam tabel berbasis bukti.",
        instruction=load_prompt("compare"),
        tools=[make_compare_pipeline(backend)],
    )
