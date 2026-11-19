import pytest

from smart_library.workflows.compare_pipeline import make_compare_pipeline
from tests.unit.fakes import FakeBackend
from tests.unit.wf_harness import run_workflow

PDP = "UU Nomor 27 Tahun 2022 tentang Pelindungan Data Pribadi.pdf"
ITE = "UU Nomor 1 Tahun 2024 tentang Perubahan Kedua atas UU ITE.pdf"


@pytest.fixture
def fake():
    return FakeBackend({
        "Regulasi Digital ID": [(PDP, "pengendali data pribadi wajib melindungi data"),
                                (ITE, "penyelenggara sistem elektronik wajib andal aman")],
        "Riset RAG": [("LightRAG.pdf", "graph retrieval data teks"), ("Resep.pdf", "rendang santan")],
    })


async def _run(fake, targets, question=""):
    out, _ = await run_workflow(make_compare_pipeline(fake), {"targets": targets, "question": question})
    return out


async def test_compare_two_documents(fake):
    out = await _run(fake, ["uu pdp", "uu ite"], "kewajiban penyelenggara pengendali")
    assert out["status"] == "success"
    assert [e["target"] for e in out["evidence"]] == [PDP, ITE]
    assert all(e["sources"] for e in out["evidence"])
    assert out["evidence"][0]["sources"][0]["document"] == PDP


async def test_compare_dataset_vs_document(fake):
    out = await _run(fake, ["Riset RAG", "uu pdp"], "data")
    assert [(e["target"], e["kind"]) for e in out["evidence"]] == [("Riset RAG", "dataset"), (PDP, "document")]
    assert all(s["dataset"] == "Riset RAG" for s in out["evidence"][0]["sources"])


async def test_compare_single_target(fake):
    out = await _run(fake, ["uu pdp"])
    assert out["status"] == "error" and "minimal 2 target" in out["message"]


async def test_compare_no_evidence(fake):
    out = await _run(fake, ["uu pdp", "Resep.pdf"], "pengendali data pribadi")
    assert out["no_evidence"] == ["Resep.pdf"]


async def test_compare_unresolved_returns_candidates(fake):
    out = await _run(fake, ["uu", "Riset RAG"])
    assert out["status"] == "needs_clarification" and set(out["unresolved"]["uu"]) == {PDP, ITE}
