from smart_library.cli.eval import render_report

ROWS = [
    {"id": "q1", "type": "fakta", "question": "Apa A?", "backend": "ragflow", "score": 5, "reason": "lengkap",
     "latency_s": 10.0, "sources": ["a.pdf"], "answer": "A adalah ..."},
    {"id": "q1", "type": "fakta", "question": "Apa A?", "backend": "lightrag", "score": 3, "reason": "kurang",
     "latency_s": 12.5, "sources": ["a.pdf", "b.pdf"], "answer": "A ..."},
    {"id": "q2", "type": "compare", "question": "Beda A dan B?", "backend": "ragflow", "score": 2, "reason": "x",
     "latency_s": 20.0, "sources": [], "answer": "..."},
    {"id": "q2", "type": "compare", "question": "Beda A dan B?", "backend": "lightrag", "score": 4, "reason": "y",
     "latency_s": 18.0, "sources": ["b.pdf"], "answer": "...", "error": None},
]


def test_render_report_summary_by_type():
    md = render_report(ROWS, date="2026-11-19")
    assert "# Hasil Evaluasi RAGFlow vs LightRAG — 2026-11-19" in md
    assert "| fakta | 5.00 | 3.00 | ragflow |" in md
    assert "| compare | 2.00 | 4.00 | lightrag |" in md
    assert "| **Total** | 3.50 | 3.50 | seri |" in md
    assert "| q1 | fakta | 5 | 3 | 10.0 | 12.5 | 1 | 2 |" in md
    assert "<details>" in md and "A adalah ..." in md


def test_merge_rows_replaces_only_rerun_backend():
    from smart_library.cli.eval import merge_rows

    old = [{"id": "q1", "backend": "ragflow", "score": 5}, {"id": "q1", "backend": "lightrag", "score": 1}]
    new = [{"id": "q1", "backend": "lightrag", "score": 4}]
    merged = merge_rows(old, new)
    assert sorted((r["backend"], r["score"]) for r in merged) == [("lightrag", 4), ("ragflow", 5)]


def test_questions_yaml_is_valid():
    from collections import Counter

    import yaml

    from smart_library.cli.eval import QUESTIONS

    qs = yaml.safe_load(QUESTIONS.read_text(encoding="utf-8"))["questions"]
    assert len(qs) == 10 and len({q["id"] for q in qs}) == 10
    assert Counter(q["type"] for q in qs) == {"fakta": 4, "compare": 3, "relasional": 3}
    assert all(q["question"] and len(q["expected_points"]) >= 3 for q in qs)


def test_merge_rows_only_rerun_keeps_other_questions():
    from smart_library.cli.eval import merge_rows

    old = [{"id": "q1", "backend": "ragflow", "score": 5}, {"id": "q2", "backend": "ragflow", "score": 1}]
    merged = merge_rows(old, [{"id": "q2", "backend": "ragflow", "score": 4}])
    assert sorted((r["id"], r["score"]) for r in merged) == [("q1", 5), ("q2", 4)]
