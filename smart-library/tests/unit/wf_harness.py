"""Menjalankan Workflow ADK tanpa LLM: node pembuka menyuntikkan request, artifact disiapkan dulu."""

from google.adk import Workflow
from google.adk.apps import App
from google.adk.runners import InMemoryRunner
from google.genai import types


async def run_workflow(workflow, request: dict, artifacts: dict[str, bytes] | None = None):
    def start(node_input) -> dict:
        return request

    harness = Workflow(name="harness", edges=[("START", start, workflow)])
    runner = InMemoryRunner(app=App(name="t", root_agent=harness))
    session = await runner.session_service.create_session(app_name="t", user_id="u")
    for name, data in (artifacts or {}).items():
        await runner.artifact_service.save_artifact(
            app_name="t", user_id="u", session_id=session.id, filename=name,
            artifact=types.Part.from_bytes(data=data, mime_type="application/octet-stream"),
        )
    last = None
    async for event in runner.run_async(
        user_id="u", session_id=session.id, new_message=types.Content(role="user", parts=[types.Part(text="go")])
    ):
        if getattr(event, "output", None) is not None:
            last = event.output
    session = await runner.session_service.get_session(app_name="t", user_id="u", session_id=session.id)
    return last, session.state
