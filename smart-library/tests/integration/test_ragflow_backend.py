"""Butuh RAGFlow asli (docker) + Azure embedding. Jalankan: uv run pytest -m integration"""

import time

import pytest

from smart_library.backends.base import BackendError
from smart_library.backends.ragflow_backend import RagflowBackend

pytestmark = pytest.mark.integration
NAME = "zz-test-smartlib"


@pytest.fixture
def backend():
    b = RagflowBackend.from_env()
    yield b
    for d in b.rag.list_datasets(name=NAME):
        b.rag.delete_datasets(ids=[d.id])


def test_upload_parse_retrieve(backend, sample_bytes):
    ds = backend.ensure_dataset(NAME, "dataset sementara untuk test")
    doc = backend.upload(ds.id, "sample.md", sample_bytes)
    backend.start_parse(ds.id, [doc.id])
    deadline = time.time() + 120
    while backend.parse_status(ds.id, [doc.id])[doc.id] != "DONE":
        assert time.time() < deadline, "parsing > 120 s"
        time.sleep(3)
    assert [d.name for d in backend.list_documents(ds.id)] == ["sample.md"]
    chunks = backend.retrieve("apa definisi data pribadi", dataset_ids=[ds.id])
    assert chunks and chunks[0].document == "sample.md" and chunks[0].dataset == NAME
    with pytest.raises(BackendError, match="sudah ada"):
        backend.upload(ds.id, "sample.md", sample_bytes)


def test_unreachable_server_gives_actionable_error():
    b = RagflowBackend("http://localhost:1", "x")
    with pytest.raises(BackendError, match="docker compose up"):
        b.list_datasets()
