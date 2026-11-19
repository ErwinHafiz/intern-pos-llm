"""Bentuk hasil yang dikirim tools ke LLM: sumber bernomor + error yang seragam."""

from smart_library.backends.base import BackendError, Chunk, Unsupported

# Batas sama untuk SEMUA backend agar perbandingan adil: chunk LightRAG (~4000 char)
# jauh lebih panjang dari chunk RAGFlow; batas 800 dulu memotong isi penting.
MAX_CHARS = 2500
BUDGET = 16000


def chunks_to_sources(chunks: list[Chunk], max_chars: int = MAX_CHARS, budget: int = BUDGET) -> list[dict]:
    """Sumber bernomor dari yang paling relevan; berhenti saat total teks melewati budget."""
    out, used = [], 0
    for c in chunks:
        text = c.text if len(c.text) <= max_chars else c.text[:max_chars] + "…"
        if out and used + len(text) > budget:
            break
        used += len(text)
        out.append({"ref": len(out) + 1, "document": c.document, "dataset": c.dataset,
                    "location": c.location, "kind": c.kind, "text": text})
    return out


def error_dict(e: BackendError) -> dict:
    return {"status": "unsupported" if isinstance(e, Unsupported) else "error", "message": str(e)}


def clarify(name: str, candidates: list[str]) -> dict:
    """Nama tidak ketemu / ambigu: minta LLM bertanya ke user, jangan menebak."""
    hint = f"Mungkin maksudnya: {', '.join(candidates)}." if candidates else "Tidak ada yang mirip. Cek dengan /dataset."
    return {"status": "needs_clarification", "name": name, "candidates": candidates,
            "message": f"'{name}' tidak bisa dipastikan. {hint}"}
