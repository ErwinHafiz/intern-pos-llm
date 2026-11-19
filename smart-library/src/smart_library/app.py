"""Merakit App ADK untuk satu backend. Dipanggil oleh agents/<nama>/agent.py."""

from google.adk.apps import App
from google.adk.plugins.save_files_as_artifacts_plugin import SaveFilesAsArtifactsPlugin

from smart_library.agents.librarian import build_librarian
from smart_library.backends.base import RagBackend
from smart_library.config import Settings, load_settings, make_model


def build_app(backend: RagBackend, settings: Settings | None = None) -> App:
    model = make_model(settings or load_settings())
    return App(
        name=f"library_{backend.name}",
        root_agent=build_librarian(backend, model),
        plugins=[SaveFilesAsArtifactsPlugin()],  # lampiran chat → artifact yang bisa dibaca ingest_pipeline
    )
