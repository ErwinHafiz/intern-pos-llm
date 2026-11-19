from google.adk.agents import LlmAgent

from smart_library.agents import load_prompt
from smart_library.tools.catalog_tools import make_catalog_tools


def build_catalog_agent(backend, model) -> LlmAgent:
    # mode="task": boleh tanya-jawab dengan user, selesai lewat finish_task lalu kembali ke librarian
    return LlmAgent(
        name="catalog_agent",
        mode="task",
        model=model,
        description="Menampilkan daftar dataset/dokumen beserta status parsing, dan menetapkan fokus (scope).",
        instruction=load_prompt("catalog"),
        tools=make_catalog_tools(backend),
    )
