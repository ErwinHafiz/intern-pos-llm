"""Agent asli: Azure LLM + RAGFlow. Memastikan routing librarian → sub-agent berjalan."""

import pytest
from google.adk.runners import InMemoryRunner
from google.genai import types

from smart_library.app import build_app
from smart_library.backends.ragflow_backend import RagflowBackend

pytestmark = pytest.mark.integration


async def _chat(app, text):
    runner = InMemoryRunner(app=app)
    session = await runner.session_service.create_session(app_name=app.name, user_id="u")
    authors, final = set(), ""
    async for ev in runner.run_async(user_id="u", session_id=session.id,
                                     new_message=types.Content(role="user", parts=[types.Part(text=text)])):
        authors.add(ev.author)
        if ev.author == "librarian" and ev.content and ev.content.parts and ev.content.parts[0].text:
            final = ev.content.parts[0].text
    return authors, final


async def test_dataset_shortcut_routes_to_catalog():
    backend = RagflowBackend.from_env()
    authors, final = await _chat(build_app(backend), "/dataset")
    assert "catalog_agent" in authors
    assert any(d.name in final for d in backend.list_datasets())
