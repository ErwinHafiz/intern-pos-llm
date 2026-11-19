from google.adk.agents import LlmAgent

from smart_library.agents import load_prompt
from smart_library.workflows.ingest_pipeline import make_ingest_pipeline


def build_ingest_agent(backend, model) -> LlmAgent:
    # mode="single_turn": dipanggil seperti tool, TIDAK melihat chat; input = permintaan dari librarian
    return LlmAgent(
        name="ingest_agent",
        mode="single_turn",
        model=model,
        description="Menyimpan file lampiran ke dataset. Input wajib berisi nama file persis dan nama dataset tujuan.",
        instruction=load_prompt("ingest"),
        tools=[make_ingest_pipeline(backend)],  # Workflow dipasang langsung sebagai tool
    )
