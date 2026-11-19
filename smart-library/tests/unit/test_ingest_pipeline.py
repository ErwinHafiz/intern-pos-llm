import pytest

from smart_library.workflows.ingest_pipeline import make_ingest_pipeline
from tests.unit.fakes import FakeBackend
from tests.unit.wf_harness import run_workflow


@pytest.fixture
def fake():
    return FakeBackend({"Riset RAG": [("LightRAG.pdf", "graph")]})


def _wf(fake, **kw):
    return make_ingest_pipeline(fake, poll_interval=0.01, **kw)


async def test_ingest_happy_path(fake):
    out, state = await run_workflow(_wf(fake), {"artifact_name": "a.pdf", "dataset": "riset rag"}, {"a.pdf": b"%PDF x"})
    assert out["status"] == "success" and out["parse_status"] == "DONE"
    assert out["dataset"] == "Riset RAG"
    assert state["last_uploaded"]["document"] == "a.pdf"
    assert "a.pdf" in [d.name for d in fake.list_documents("ds0")]


async def test_ingest_new_dataset_is_created(fake):
    out, _ = await run_workflow(_wf(fake), {"artifact_name": "a.pdf", "dataset": "Koleksi Baru"}, {"a.pdf": b"%PDF x"})
    assert out["status"] == "success" and out["dataset"] == "Koleksi Baru"


async def test_ingest_missing_artifact(fake):
    out, _ = await run_workflow(_wf(fake), {"artifact_name": "tidak-ada.pdf", "dataset": "Riset RAG"})
    assert out["status"] == "error" and "Lampirkan file" in out["message"]


async def test_ingest_unsupported_ext(fake):
    out, _ = await run_workflow(_wf(fake), {"artifact_name": "x.exe", "dataset": "Riset RAG"}, {"x.exe": b"MZ"})
    assert out["status"] == "unsupported" and ".pdf" in out["message"]


async def test_ingest_duplicate(fake):
    await run_workflow(_wf(fake), {"artifact_name": "a.pdf", "dataset": "Riset RAG"}, {"a.pdf": b"%PDF x"})
    out, _ = await run_workflow(_wf(fake), {"artifact_name": "a.pdf", "dataset": "Riset RAG"}, {"a.pdf": b"%PDF x"})
    assert out["status"] == "error" and "sudah ada" in out["message"]


async def test_ingest_timeout_reports_running(fake):
    fake.parse_result = "RUNNING"
    out, state = await run_workflow(_wf(fake, timeout=0.05), {"artifact_name": "a.pdf", "dataset": "Riset RAG"}, {"a.pdf": b"%PDF x"})
    assert out["status"] == "success" and out["parse_status"] == "RUNNING"
    assert "/dataset" in out["message"] and state["last_uploaded"]["status"] == "RUNNING"


async def test_ingest_parse_failed(fake):
    fake.parse_result = "FAIL"
    out, _ = await run_workflow(_wf(fake), {"artifact_name": "a.pdf", "dataset": "Riset RAG"}, {"a.pdf": b"%PDF x"})
    assert out["status"] == "error" and out["parse_status"] == "FAIL"


@pytest.mark.parametrize("name", ["Riset LLM", "Riset RAG 2025"])
async def test_ingest_similar_new_name_asks_instead_of_guessing(fake, name):
    out, _ = await run_workflow(_wf(fake), {"artifact_name": "a.pdf", "dataset": name}, {"a.pdf": b"%PDF x"})
    assert out["status"] == "needs_clarification" and "Riset RAG" in out["candidates"]
    assert "create_new" in out["message"]
    assert [d.name for d in fake.list_documents("ds0")] == ["LightRAG.pdf"]


async def test_ingest_create_new_flag_creates_dataset(fake):
    out, _ = await run_workflow(_wf(fake), {"artifact_name": "a.pdf", "dataset": "Riset LLM", "create_new": True},
                                {"a.pdf": b"%PDF x"})
    assert out["status"] == "success" and out["dataset"] == "Riset LLM"
