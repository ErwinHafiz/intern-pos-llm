"""Butuh LightRAG Server asli (`uv run lightrag-up`) + Azure. Jalankan: uv run pytest -m integration"""

import time

import pytest

from smart_library.backends.base import BackendError, Unsupported
from smart_library.backends.lightrag_backend import LightragBackend

pytestmark = pytest.mark.integration


@pytest.fixture
def backend():
    b = LightragBackend.from_env()
    ds = b.list_datasets()[-1].id
    yield b, ds
    ids = [d.id for d in b.list_documents(ds) if d.name == "sample.md"]
    if ids:
        b._client(ds).request("DELETE", "/documents/delete_document", json={"doc_ids": ids, "delete_file": True})


def test_upload_parse_retrieve(backend, sample_bytes):
    b, ds = backend
    doc = b.upload(ds, "sample.md", sample_bytes)
    deadline = time.time() + 300
    while (status := b.parse_status(ds, [doc.id])[doc.id]) != "DONE":
        assert status != "FAIL" and time.time() < deadline, status
        time.sleep(5)
    sample = next(d for d in b.list_documents(ds) if d.name == "sample.md")
    chunks = b.retrieve("apa definisi data pribadi", dataset_ids=[ds], document_ids=[sample.id])
    assert chunks and chunks[0].kind == "chunk" and chunks[0].document == "sample.md"
    assert {"entity", "relation"} & {c.kind for c in chunks}
    with pytest.raises(BackendError, match="sudah ada"):
        b.upload(ds, "sample.md", sample_bytes)


def test_new_dataset_unsupported():
    with pytest.raises(Unsupported, match="LIGHTRAG_WORKSPACES"):
        LightragBackend.from_env().ensure_dataset("Koleksi Baru")


def test_server_down_is_actionable():
    with pytest.raises(BackendError, match="lightrag-up"):
        LightragBackend({"X": "http://localhost:1"}).list_datasets()
