from importlib import resources

from smart_library.app import build_app
from smart_library.config import Settings
from tests.unit.fakes import FakeBackend

SETTINGS = Settings(llm_model="openai/gpt-5.1", llm_api_base="https://x/openai/v1", llm_api_key="k")


def _app():
    return build_app(FakeBackend({"A": []}), SETTINGS)


def test_build_app_structure():
    app = _app()
    root = app.root_agent
    assert app.name == "library_fake" and root.name == "librarian"
    modes = {a.name: a.mode for a in root.sub_agents}
    assert modes == {"catalog_agent": "task", "ingest_agent": "single_turn",
                     "research_agent": "chat", "compare_agent": "task"}
    assert any(p.name == "save_files_as_artifacts_plugin" for p in app.plugins)


def test_workflows_are_tools():
    subs = {a.name: a for a in _app().root_agent.sub_agents}
    names = lambda agent: {getattr(t, "name", getattr(t, "__name__", "")) for t in agent.tools}
    assert "ingest_pipeline" in names(subs["ingest_agent"])
    assert "compare_pipeline" in names(subs["compare_agent"])
    assert {"search", "read_document", "set_scope"} <= names(subs["research_agent"])
    assert {"list_datasets", "list_documents", "set_scope"} <= names(subs["catalog_agent"])


def test_librarian_knows_backend_name():
    assert "fake" in _app().root_agent.instruction


def test_prompts_complete():
    files = list(resources.files("smart_library.prompts").iterdir())
    md = [f for f in files if f.name.endswith(".md")]
    assert {f.name for f in md} == {"librarian.md", "catalog.md", "ingest.md", "research.md", "compare.md"}
    for f in md:
        text = f.read_text(encoding="utf-8")
        assert len(text) > 300 and "TODO" not in text
        assert "{" not in text, f"{f.name}: kurung kurawal dianggap placeholder state oleh ADK"
