"""`uv run eval [--backend ragflow|lightrag|all] [--only q1,q2]`

Pertanyaan yang sama (eval/questions.yaml) dikirim ke agent RAGFlow dan agent LightRAG.
Agent, prompt, dan LLM identik, jadi bedanya murni di retrieval. Tiap jawaban dinilai 1–5
oleh LLM-judge dengan prompt tetap terhadap `expected_points` yang diambil dari dokumen asli.
Hasil: eval/results/<tanggal>.md (+ .json).
"""

import argparse
import asyncio
import datetime as dt
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import litellm
import yaml
from google.adk.runners import InMemoryRunner
from google.genai import types

from smart_library.config import PROJECT_ROOT, load_settings

QUESTIONS = PROJECT_ROOT / "eval" / "questions.yaml"
RESULTS = PROJECT_ROOT / "eval" / "results"
SOURCE_TOOLS = {"search", "read_document", "compare_pipeline"}

JUDGE_PROMPT = """Kamu penilai jawaban sistem RAG. Nilai JAWABAN terhadap POIN KUNCI yang seharusnya ada.
Skor 1-5: 5 = semua poin benar & bersumber; 4 = hampir semua; 3 = sebagian; 2 = sedikit; 1 = salah/tidak menjawab.
Jawaban yang jujur berkata "tidak ditemukan" padahal poin ada di dokumen = 1. Jangan menilai gaya bahasa.
Balas HANYA JSON: {{"skor": <1-5>, "alasan": "<satu kalimat>"}}

PERTANYAAN: {question}
POIN KUNCI:
{points}
JAWABAN:
{answer}"""


def _sources_from(response: dict) -> list[str]:
    docs = [s["document"] for s in response.get("sources", [])]
    for ev in response.get("evidence", []):
        docs += [s["document"] for s in ev.get("sources", [])]
    return docs


async def run_question(app, question: str) -> dict:
    runner = InMemoryRunner(app=app)
    session = await runner.session_service.create_session(app_name=app.name, user_id="eval")
    answer, sources, agents = "", [], set()
    start = time.perf_counter()
    async for ev in runner.run_async(user_id="eval", session_id=session.id,
                                     new_message=types.Content(role="user", parts=[types.Part(text=question)])):
        agents.add(ev.author)
        for part in ev.content.parts if ev.content and ev.content.parts else []:
            if part.function_response and part.function_response.name in SOURCE_TOOLS:
                sources += _sources_from(part.function_response.response or {})
            elif part.text and ev.author != "user" and not getattr(ev, "partial", False):
                answer = part.text
    return {"answer": answer, "sources": sorted(set(sources)),
            "latency_s": round(time.perf_counter() - start, 1), "agents": sorted(agents - {"user"})}


def judge(settings, question: str, points: list[str], answer: str) -> tuple[int, str]:
    resp = litellm.completion(
        model=settings.llm_model, api_base=settings.llm_api_base, api_key=settings.llm_api_key,
        api_version=settings.llm_api_version or None,
        messages=[{"role": "user", "content": JUDGE_PROMPT.format(
            question=question, points="\n".join(f"- {p}" for p in points), answer=answer or "(kosong)")}],
        response_format={"type": "json_object"},
    )
    data = json.loads(resp.choices[0].message.content)
    return int(data["skor"]), str(data["alasan"])


def merge_rows(old: list[dict], new: list[dict]) -> list[dict]:
    """Gabung hasil run: pasangan (pertanyaan, backend) yang dijalankan ulang menggantikan yang lama."""
    rerun = {(r["id"], r["backend"]) for r in new}
    rows = [r for r in old if (r["id"], r["backend"]) not in rerun] + new
    return sorted(rows, key=lambda r: (int("".join(filter(str.isdigit, r["id"])) or 0), r["backend"]))


def _winner(a: float, b: float) -> str:
    return "seri" if abs(a - b) < 1e-9 else ("ragflow" if a > b else "lightrag")


def render_report(rows: list[dict], date: str) -> str:
    by = {(r["id"], r["backend"]): r for r in rows}
    ids = list(dict.fromkeys(r["id"] for r in rows))
    types_ = list(dict.fromkeys(r["type"] for r in rows))
    mean = lambda xs: sum(xs) / len(xs) if xs else 0.0  # noqa: E731
    score = lambda backend, t=None: mean(  # noqa: E731
        [r["score"] for r in rows if r["backend"] == backend and (t is None or r["type"] == t)])

    out = [f"# Hasil Evaluasi RAGFlow vs LightRAG — {date}", "",
           "Agent, prompt, dan LLM sama; yang berbeda hanya backend retrieval. Skor 1–5 oleh LLM-judge.", "",
           "## Ringkasan per jenis pertanyaan", "",
           "| Jenis | RAGFlow | LightRAG | Unggul |", "|---|---|---|---|"]
    for t in types_:
        a, b = score("ragflow", t), score("lightrag", t)
        out.append(f"| {t} | {a:.2f} | {b:.2f} | {_winner(a, b)} |")
    a, b = score("ragflow"), score("lightrag")
    out.append(f"| **Total** | {a:.2f} | {b:.2f} | {_winner(a, b)} |")
    lat = {k: mean([r["latency_s"] for r in rows if r["backend"] == k]) for k in ("ragflow", "lightrag")}
    out += ["", f"Rata-rata latensi: RAGFlow {lat['ragflow']:.1f} s · LightRAG {lat['lightrag']:.1f} s", "",
            "## Per pertanyaan", "",
            "| ID | Jenis | Skor RF | Skor LR | Latensi RF (s) | Latensi LR (s) | #Sumber RF | #Sumber LR |",
            "|---|---|---|---|---|---|---|---|"]
    for i in ids:
        rf, lr = by.get((i, "ragflow"), {}), by.get((i, "lightrag"), {})
        t = (rf or lr)["type"]
        out.append(f"| {i} | {t} | {rf.get('score', '-')} | {lr.get('score', '-')} | {rf.get('latency_s', '-')} | "
                   f"{lr.get('latency_s', '-')} | {len(rf.get('sources', []))} | {len(lr.get('sources', []))} |")
    out += ["", "## Jawaban lengkap", ""]
    for i in ids:
        q = next(r for r in rows if r["id"] == i)
        out += [f"### {i}: {q['question']}", ""]
        for backend in ("ragflow", "lightrag"):
            r = by.get((i, backend))
            if not r:
                continue
            note = f" — ERROR: {r['error']}" if r.get("error") else ""
            out += [f"<details><summary><b>{backend}</b> · skor {r['score']} · {r['reason']}{note}</summary>", "",
                    r["answer"] or "(kosong)", "", f"Sumber: {', '.join(r['sources']) or '-'}", "", "</details>", ""]
    return "\n".join(out)


async def _evaluate(backends: list[str], only: set[str]) -> list[dict]:
    from smart_library.app import build_app
    from smart_library.backends.lightrag_backend import LightragBackend
    from smart_library.backends.ragflow_backend import RagflowBackend

    settings = load_settings()
    questions = [q for q in yaml.safe_load(QUESTIONS.read_text(encoding="utf-8"))["questions"]
                 if not only or q["id"] in only]
    factories = {"ragflow": RagflowBackend.from_env, "lightrag": LightragBackend.from_env}
    rows = []
    for name in backends:
        app = build_app(factories[name](), settings)
        for q in questions:
            print(f"[{name}] {q['id']} {q['question'][:60]}…", flush=True)
            row = {"id": q["id"], "type": q["type"], "question": q["question"], "backend": name}
            try:
                row |= await run_question(app, q["question"])
                row["score"], row["reason"] = judge(settings, q["question"], q["expected_points"], row["answer"])
            except Exception as e:  # satu pertanyaan gagal tidak boleh menghentikan evaluasi
                row |= {"answer": "", "sources": [], "latency_s": 0.0, "score": 0, "reason": "error", "error": repr(e)}
            print(f"    skor {row['score']} · {row['latency_s']} s · {len(row['sources'])} sumber", flush=True)
            rows.append(row)
    return rows


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="Bandingkan RAGFlow vs LightRAG dengan pertanyaan yang sama")
    p.add_argument("--backend", choices=["ragflow", "lightrag", "all"], default="all")
    p.add_argument("--only", default="", help="id pertanyaan dipisah koma, mis. q1,q5")
    args = p.parse_args()
    backends = ["ragflow", "lightrag"] if args.backend == "all" else [args.backend]
    rows = asyncio.run(_evaluate(backends, set(filter(None, args.only.split(",")))))
    date = dt.date.today().isoformat()
    RESULTS.mkdir(parents=True, exist_ok=True)
    out_json = RESULTS / f"{date}.json"
    if out_json.exists():  # backend boleh dijalankan bergantian (hemat RAM): gabungkan
        rows = merge_rows(json.loads(out_json.read_text(encoding="utf-8")), rows)
    (RESULTS / f"{date}.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    (RESULTS / f"{date}.md").write_text(render_report(rows, date), encoding="utf-8")
    print(f"Laporan: eval/results/{date}.md")


if __name__ == "__main__":
    main()
