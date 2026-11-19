from pathlib import Path

import pytest

from smart_library.backends.base import BackendError
from smart_library.cli.seed import SeedError, download, load_sources, looks_valid, seed_backend
from tests.unit.fakes import FakeBackend

ROOT = Path(__file__).resolve().parents[2]


def test_load_sources_schema():
    datasets = load_sources(ROOT / "data" / "sources.yaml")
    assert [d["name"] for d in datasets] == ["Regulasi Digital ID", "Riset RAG"]
    docs = [doc for d in datasets for doc in d["documents"]]
    assert all(doc["url"].startswith("https://") and doc["filename"] and doc["format"] for doc in docs)
    assert {doc["format"] for doc in docs} >= {"pdf", "docx", "csv"}
    assert len({doc["filename"] for doc in docs}) == len(docs)


def test_magic_bytes_rejects_html(tmp_path):
    page = tmp_path / "x.pdf"
    page.write_bytes(b"<!DOCTYPE html><html>blocked</html>")
    assert not looks_valid(page, "pdf")
    good = tmp_path / "y.pdf"
    good.write_bytes(b"%PDF-1.7 ...")
    assert looks_valid(good, "pdf")
    assert not looks_valid(tmp_path / "missing.csv", "csv")
    csv = tmp_path / "z.csv"
    csv.write_text("<html>")
    assert not looks_valid(csv, "csv")


def test_download_skips_existing_valid(tmp_path):
    (tmp_path / "a.pdf").write_bytes(b"%PDF-1.4")
    doc = {"url": "https://invalid.invalid/a.pdf", "filename": "a.pdf", "format": "pdf", "page": "https://p"}
    assert download(doc, tmp_path) == tmp_path / "a.pdf"  # tidak menyentuh jaringan


def test_download_failure_gives_manual_instruction(tmp_path):
    doc = {"url": "https://invalid.invalid/a.pdf", "filename": "a.pdf", "format": "pdf", "page": "https://halaman"}
    with pytest.raises(SeedError, match="https://halaman"):
        download(doc, tmp_path)


def test_seed_backend_is_idempotent(tmp_path):
    (tmp_path / "a.pdf").write_bytes(b"%PDF-1.4 isi")
    sources = [{"name": "Riset RAG", "description": "d",
                "documents": [{"filename": "a.pdf", "format": "pdf", "url": "https://x", "page": "https://x"}]}]
    fake = FakeBackend({})
    seed_backend(fake, sources, tmp_path, poll_interval=0)
    seed_backend(fake, sources, tmp_path, poll_interval=0)
    ds = [d for d in fake.list_datasets() if d.name == "Riset RAG"][0]
    assert [d.name for d in fake.list_documents(ds.id)] == ["a.pdf"]


def test_seed_survives_transient_poll_error(tmp_path):
    (tmp_path / "a.pdf").write_bytes(b"%PDF-1.4 isi")
    sources = [{"name": "Riset RAG", "description": "d",
                "documents": [{"filename": "a.pdf", "format": "pdf", "url": "https://x", "page": "https://x"}]}]
    fake = FakeBackend({}, parse_result="RUNNING")
    calls = {"n": 0}

    def flaky(ds, ids):
        calls["n"] += 1
        if calls["n"] == 1:
            raise BackendError("RAGFlow respons tidak valid (sementara)")
        return {i: "DONE" for i in ids}

    fake.parse_status = flaky
    results = seed_backend(fake, sources, tmp_path, poll_interval=0)
    assert results == {"a.pdf": "DONE"} and calls["n"] == 2
