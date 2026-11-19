"""Workflow bandingkan: resolve_targets ─┬─(ok)──▶ retrieve_target ×N (paralel) ─▶ build_evidence
                                       └─(stop)─▶ stop

- Routing: resolve_targets memilih rute lewat `ctx.route` (sama seperti router di graph_based_agent).
- Fan-out dinamis: `@node(parallel_worker=True)` menjalankan retrieve_target untuk SETIAP item list
  secara paralel dan mengumpulkan hasilnya jadi list (berbeda dengan JoinNode yang menggabungkan
  cabang statis yang sudah ditulis di edges).
"""

import asyncio
from dataclasses import asdict

from google.adk import Workflow
from google.adk.agents.context import Context
from google.adk.workflow import node
from pydantic import BaseModel, Field

from smart_library.backends.base import BackendError, RagBackend
from smart_library.naming import resolve_names
from smart_library.tools.formatting import chunks_to_sources, error_dict

DEFAULT_QUESTION = "poin utama, tujuan, ruang lingkup, dan ketentuan penting"


class CompareRequest(BaseModel):
    targets: list[str] = Field(description="Nama 2+ dataset/dokumen yang dibandingkan, boleh campur")
    question: str = Field(default="", description="Fokus perbandingan (opsional)")


def make_compare_pipeline(backend: RagBackend, top_k: int = 6) -> Workflow:
    async def resolve_targets(ctx: Context, node_input: CompareRequest):
        if len(node_input.targets) < 2:
            ctx.route = "stop"
            return {"status": "error", "message": "Butuh minimal 2 target untuk dibandingkan (dataset atau dokumen)."}
        try:
            targets, unresolved = await asyncio.to_thread(resolve_names, backend, node_input.targets)
        except BackendError as e:
            ctx.route = "stop"
            return error_dict(e)
        if unresolved:
            ctx.route = "stop"
            return {"status": "needs_clarification", "unresolved": unresolved,
                    "message": "Beberapa target belum pasti. Tanyakan ke user dengan menawarkan kandidat."}
        ctx.route = "ok"
        question = node_input.question or DEFAULT_QUESTION
        return [{"target": asdict(t), "question": question} for t in targets]

    @node(parallel_worker=True)
    async def retrieve_target(node_input: dict) -> dict:
        t, question = node_input["target"], node_input["question"]
        doc_ids = [t["id"]] if t["kind"] == "document" else None
        try:
            chunks = await asyncio.to_thread(
                backend.retrieve, question, dataset_ids=[t["dataset_id"]], document_ids=doc_ids, top_k=top_k
            )
        except BackendError as e:
            return {"target": t["label"], "kind": t["kind"], "sources": [], "error": str(e)}
        return {"target": t["label"], "kind": t["kind"], "question": question, "sources": chunks_to_sources(chunks)}

    def build_evidence(node_input: list) -> dict:
        errors = [e["error"] for e in node_input if e.get("error")]
        if errors:
            return {"status": "error", "message": errors[0]}
        return {
            "status": "success",
            "question": node_input[0]["question"],
            "evidence": [{k: e[k] for k in ("target", "kind", "sources")} for e in node_input],
            "no_evidence": [e["target"] for e in node_input if not e["sources"]],
            "instruction": "Isi sel tabel hanya dari sources; target di no_evidence ditulis 'tidak ditemukan di sumber'.",
        }

    def stop(node_input: dict) -> dict:
        return node_input

    return Workflow(
        name="compare_pipeline",
        description="Ambil bukti dari 2+ dataset/dokumen secara paralel untuk dibandingkan.",
        edges=[
            ("START", resolve_targets),
            (resolve_targets, {"ok": retrieve_target, "stop": stop}),
            (retrieve_target, build_evidence),
        ],
        input_schema=CompareRequest,
    )
