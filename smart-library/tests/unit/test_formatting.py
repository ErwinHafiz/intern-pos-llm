from smart_library.backends.base import BackendError, Chunk, Unsupported
from smart_library.tools.formatting import chunks_to_sources, error_dict


def _c(text, doc="a.pdf"):
    return Chunk(text, doc, "Riset RAG", 0.9, "hlm. 3")


def test_sources_numbered_from_1():
    out = chunks_to_sources([_c("x"), _c("y", "b.pdf")])
    assert [s["ref"] for s in out] == [1, 2]
    assert out[1] == {"ref": 2, "document": "b.pdf", "dataset": "Riset RAG", "location": "hlm. 3", "kind": "chunk", "text": "y"}


def test_text_truncated_with_ellipsis():
    out = chunks_to_sources([_c("a" * 900)], max_chars=800)
    assert len(out[0]["text"]) == 801 and out[0]["text"].endswith("…")


def test_error_dict_unsupported():
    assert error_dict(Unsupported("tidak bisa")) == {"status": "unsupported", "message": "tidak bisa"}
    assert error_dict(BackendError("mati"))["status"] == "error"


def test_sources_have_equal_total_budget():
    long = [_c("x" * 4000, f"d{i}.pdf") for i in range(10)]
    out = chunks_to_sources(long, max_chars=2500, budget=6000)
    assert all(len(s["text"]) <= 2501 for s in out)
    assert sum(len(s["text"]) for s in out) <= 6000 + len(out)
    assert [s["ref"] for s in out] == list(range(1, len(out) + 1))
