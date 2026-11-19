import pytest

from smart_library.backends.base import BackendError, find_dataset
from tests.unit.fakes import FakeBackend


@pytest.fixture
def fake():
    return FakeBackend({
        "Regulasi Digital ID": [("UU PDP.pdf", "data pribadi wajib dilindungi pengendali data")],
        "Riset RAG": [("LightRAG.pdf", "graph retrieval augmented generation")],
    })


def test_find_dataset_case_insensitive(fake):
    assert find_dataset(fake, "riset rag").name == "Riset RAG"


def test_find_dataset_missing_lists_available(fake):
    with pytest.raises(BackendError) as e:
        find_dataset(fake, "Hukum")
    assert "Regulasi Digital ID" in str(e.value) and "Riset RAG" in str(e.value)


def test_fake_retrieve_respects_document_filter(fake):
    ds = find_dataset(fake, "Riset RAG")
    doc = fake.list_documents(ds.id)[0]
    chunks = fake.retrieve("data graph", document_ids=[doc.id])
    assert chunks and all(c.document == "LightRAG.pdf" for c in chunks)
