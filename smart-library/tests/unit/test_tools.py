from types import SimpleNamespace

import pytest

from smart_library.tools.catalog_tools import make_catalog_tools
from smart_library.tools.research_tools import make_research_tools
from tests.unit.fakes import FakeBackend

PDP = "UU Nomor 27 Tahun 2022 tentang Pelindungan Data Pribadi.pdf"


@pytest.fixture
def fake():
    return FakeBackend({
        "Regulasi Digital ID": [(PDP, "data pribadi wajib dilindungi pengendali data pribadi")],
        "Riset RAG": [("LightRAG.pdf", "graph retrieval untuk data teks")],
    })


@pytest.fixture
def ctx():
    return SimpleNamespace(state={})


def _tools(fake):
    return {f.__name__: f for f in make_catalog_tools(fake) + make_research_tools(fake)}


def test_list_datasets_shape(fake):
    out = _tools(fake)["list_datasets"]()
    assert out["status"] == "success"
    assert {"name": "Riset RAG", "description": "", "documents": 1} in out["datasets"]


def test_list_documents_loose_name(fake):
    out = _tools(fake)["list_documents"]("regulasi digital")
    assert out["status"] == "success" and out["documents"][0]["name"] == PDP


def test_set_scope_then_search_is_scoped(fake, ctx):
    t = _tools(fake)
    assert t["set_scope"](tool_context=ctx, dataset="riset rag")["status"] == "success"
    out = t["search"]("data", tool_context=ctx)
    assert out["scope"] == "Riset RAG"
    assert out["sources"] and all(s["dataset"] == "Riset RAG" for s in out["sources"])
    t["set_scope"](tool_context=ctx)  # kosong = reset
    assert t["search"]("data", tool_context=ctx)["scope"] == "semua dataset"


def test_set_scope_document(fake, ctx):
    out = _tools(fake)["set_scope"](tool_context=ctx, document="uu pdp")
    assert out["status"] == "success" and ctx.state["scope"]["label"] == PDP
    assert len(ctx.state["scope"]["documents"]) == 1


def test_search_no_results_says_not_found(fake, ctx):
    out = _tools(fake)["search"]("resep rendang", tool_context=ctx)
    assert out["status"] == "success" and out["sources"] == [] and "tidak ditemukan" in out["message"]


def test_read_document_sets_scope_for_follow_ups(fake, ctx):
    t = _tools(fake)
    out = t["read_document"]("uu pdp", tool_context=ctx, focus="data pribadi")
    assert out["status"] == "success" and out["document"] == PDP and out["sources"]
    assert ctx.state["scope"]["label"] == PDP
    assert all(s["document"] == PDP for s in t["search"]("data", tool_context=ctx)["sources"])


def test_unknown_name_needs_clarification(fake, ctx):
    out = _tools(fake)["read_document"]("resep masakan", tool_context=ctx)
    assert out["status"] == "needs_clarification" and "candidates" in out


def test_tools_backend_down(fake, ctx):
    fake.down = True
    t = _tools(fake)
    results = [
        t["list_datasets"](), t["list_documents"]("riset rag"), t["set_scope"](tool_context=ctx, dataset="x"),
        t["search"]("data", tool_context=ctx), t["read_document"]("uu pdp", tool_context=ctx),
    ]
    for r in results:
        assert r["status"] == "error" and "docker compose up" in r["message"]
