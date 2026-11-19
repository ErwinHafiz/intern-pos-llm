import pytest

from smart_library.naming import resolve_names, resolve_one
from tests.unit.fakes import FakeBackend

PDP = "UU Nomor 27 Tahun 2022 tentang Pelindungan Data Pribadi.pdf"
ITE = "UU Nomor 1 Tahun 2024 tentang Perubahan Kedua atas UU ITE.pdf"
LIGHT = "LightRAG - Simple and Fast RAG.pdf"
GRAPH = "GraphRAG - From Local to Global.pdf"


@pytest.fixture
def fake():
    return FakeBackend({
        "Regulasi Digital ID": [(PDP, "x"), (ITE, "x")],
        "Riset RAG": [(LIGHT, "x"), (GRAPH, "x")],
    })


def _one(fake, name):
    targets, unresolved = resolve_names(fake, [name])
    assert not unresolved, unresolved
    return targets[0]


def test_resolve_exact(fake):
    t = _one(fake, LIGHT)
    assert (t.kind, t.label) == ("document", LIGHT)


def test_resolve_loose_names(fake):
    assert _one(fake, "uu pdp").label == PDP
    assert _one(fake, "UU ITE").label == ITE
    assert _one(fake, "paper lightrag").label == LIGHT
    assert _one(fake, "graphrag").label == GRAPH


def test_resolve_dataset_vs_document(fake):
    t = _one(fake, "Riset RAG")
    assert t.kind == "dataset" and t.dataset_id == t.id
    assert _one(fake, "dataset regulasi digital").kind == "dataset"


def test_resolve_document_carries_dataset_id(fake):
    t = _one(fake, "uu pdp")
    ds = [d for d in fake.list_datasets() if d.name == "Regulasi Digital ID"][0]
    assert t.dataset_id == ds.id


def test_resolve_ambiguous_returns_candidates(fake):
    targets, unresolved = resolve_names(fake, ["uu"])
    assert targets == [] and set(unresolved["uu"]) == {PDP, ITE}


def test_resolve_typo_single_candidate(fake):
    targets, unresolved = resolve_names(fake, ["lightrga"])  # typo, satu kandidat
    assert not unresolved and targets[0].label == LIGHT


def test_resolve_unknown_returns_empty_candidates(fake):
    _, unresolved = resolve_names(fake, ["resep masakan"])
    assert unresolved["resep masakan"] == []


def test_resolve_fuzzy_tie_is_ambiguous():
    fake = FakeBackend({"A": [("LightRAG paper.pdf", "x"), ("LightRAG slides.pdf", "x")]})
    targets, unresolved = resolve_names(fake, ["lightrga"])
    assert targets == [] and set(unresolved["lightrga"]) == {"LightRAG paper.pdf", "LightRAG slides.pdf"}


def test_substring_matches_whole_words_only():
    fake = FakeBackend({"Lain": [("AI Policy.docx", "x")]})
    t, unresolved = resolve_one(fake, "ai")
    assert t is not None and t.label == "AI Policy.docx"


def test_strict_dataset_match_rejects_fuzzy(fake):
    t, candidates = resolve_one(fake, "Riset LLM", kind="dataset", strict=True)
    assert t is None and candidates == ["Riset RAG"]
    t, _ = resolve_one(fake, "riset rag", kind="dataset", strict=True)
    assert t is not None and t.label == "Riset RAG"
