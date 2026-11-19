import json
from pathlib import Path

import pytest

from smart_library.backends.base import Chunk
from smart_library.backends.lightrag_backend import filter_by_documents, map_doc_status, query_data_to_chunks

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "lightrag_query_data.json"


@pytest.mark.parametrize("raw,expected", [
    ("processed", "DONE"), ("processing", "RUNNING"), ("parsing", "RUNNING"), ("analyzing", "RUNNING"),
    ("preprocessed", "RUNNING"), ("pending", "PENDING"), ("failed", "FAIL"), ("DocStatus.PROCESSED", "DONE"),
])
def test_map_doc_status(raw, expected):
    assert map_doc_status(raw) == expected


def test_query_data_to_chunks_kinds():
    chunks = query_data_to_chunks(json.loads(FIXTURE.read_text(encoding="utf-8")), "Regulasi Digital ID", top_k=4)
    kinds = [c.kind for c in chunks]
    assert kinds[0] == "chunk" and "entity" in kinds and "relation" in kinds
    assert all(c.dataset == "Regulasi Digital ID" for c in chunks)
    first = chunks[0]
    assert first.document == "sample.md" and "Data Pribadi" in first.text
    ent = next(c for c in chunks if c.kind == "entity")
    assert ent.text.startswith("Data Pribadi: ")
    rel = next(c for c in chunks if c.kind == "relation")
    assert " → " in rel.text
    scores = [c.score for c in chunks]
    assert scores == sorted(scores, reverse=True)


def test_document_filter_on_file_path():
    chunks = [
        Chunk("a", "a.pdf", "D", 1.0), Chunk("b", "b.pdf", "D", 0.9),
        Chunk("e", "a.pdf<SEP>c.pdf", "D", 0.8, kind="entity"),
    ]
    kept = filter_by_documents(chunks, {"a.pdf"})
    assert [c.text for c in kept] == ["a", "e"]
    assert kept[1].document == "a.pdf"


def _server(chunks):
    import httpx

    def handler(request):
        if request.url.path == "/query/data":
            return httpx.Response(200, json={"status": "success", "data": {
                "chunks": [{"content": t, "file_path": f} for t, f in chunks], "entities": [], "relationships": []}})
        return httpx.Response(200, json={"documents": []})
    return httpx.Client(base_url="http://x", transport=httpx.MockTransport(handler))


def test_multi_workspace_results_ranked_by_embedding_similarity():
    from smart_library.backends.lightrag_backend import LightragBackend

    def embed(texts):  # vektor sederhana: apakah teks menyebut "data pribadi"
        return [[1.0, 0.0] if "data pribadi" in t.lower() else [0.0, 1.0] for t in texts]

    b = LightragBackend({}, embed=embed)
    b.clients = {
        "Regulasi": _server([("Pasal 1: Data Pribadi adalah data tentang orang", "uu.pdf")]),
        "Riset": _server([("graph retrieval paper", "a.pdf"), ("survey of RAG", "b.pdf")]),
    }
    chunks = b.retrieve("apa definisi data pribadi", top_k=2)
    assert chunks[0].document == "uu.pdf" and chunks[0].dataset == "Regulasi"
    assert len([c for c in chunks if c.kind == "chunk"]) == 2



def test_embedding_failure_is_reported_as_embedding_error():
    import httpx

    from smart_library.backends.base import BackendError
    from smart_library.backends.lightrag_backend import LightragBackend

    def embed(texts):
        raise httpx.ConnectError("down", request=httpx.Request("POST", "https://azure.example/openai/v1/embeddings"))

    b = LightragBackend({}, embed=embed)
    b.clients = {"A": _server([("a", "a.pdf")]), "B": _server([("b", "b.pdf")])}
    with pytest.raises(BackendError, match="Embedding") as e:
        b.retrieve("q")
    assert "lightrag-up" not in str(e.value)


def test_unexpected_response_is_backend_error_not_traceback():
    import httpx

    from smart_library.backends.base import BackendError
    from smart_library.backends.lightrag_backend import LightragBackend

    b = LightragBackend({})
    b.clients = {"A": httpx.Client(base_url="http://x", transport=httpx.MockTransport(
        lambda r: httpx.Response(200, text="<html>bad gateway</html>")))}
    with pytest.raises(BackendError, match="tidak terduga"):
        b.list_datasets()


def test_document_filter_requests_wider_retrieval():
    import httpx

    from smart_library.backends.lightrag_backend import LightragBackend

    seen = {}

    def handler(request):
        import json as _j
        if request.url.path == "/query/data":
            seen.update(_j.loads(request.content))
            return httpx.Response(200, json={"data": {"chunks": [], "entities": [], "relationships": []}})
        return httpx.Response(200, json={"documents": [{"id": "d1", "file_path": "a.pdf", "status": "processed"}]})

    b = LightragBackend({})
    b.clients = {"A": httpx.Client(base_url="http://x", transport=httpx.MockTransport(handler))}
    b.retrieve("q", dataset_ids=["A"], document_ids=["d1"], top_k=6)
    assert seen["chunk_top_k"] >= 18
