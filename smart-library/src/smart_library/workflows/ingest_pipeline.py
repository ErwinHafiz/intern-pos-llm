"""Workflow upload: START → load_file → upload → start_parse → wait_parsed → report.

Langkahnya selalu sama, jadi pakai graph Workflow (tanpa LLM): murah, cepat, dan
tiap node terlihat di tab Trace `adk web`. Dipasang sebagai tool di ingest_agent.

Konvensi: setiap node mengembalikan dict ber-"status". Kalau status bukan
"success", node berikutnya meneruskan dict itu apa adanya (short-circuit).
"""

import asyncio
import time
from pathlib import PurePath

from google.adk import Workflow
from google.adk.agents.context import Context
from pydantic import BaseModel, Field

from smart_library.backends.base import BackendError, RagBackend
from smart_library.naming import resolve_one
from smart_library.tools.formatting import clarify, error_dict

SUPPORTED_EXT = {".pdf", ".docx", ".xlsx", ".pptx", ".txt", ".md", ".csv", ".html"}


class IngestRequest(BaseModel):
    artifact_name: str = Field(description="Nama file lampiran persis seperti di placeholder chat")
    dataset: str = Field(description="Nama dataset tujuan, persis seperti disebut user")
    create_new: bool = Field(default=False, description="True hanya bila user mengonfirmasi membuat dataset BARU")


def make_ingest_pipeline(backend: RagBackend, poll_interval: float = 5, timeout: float = 300) -> Workflow:
    async def load_file(ctx: Context, node_input: IngestRequest) -> dict:
        name = node_input.artifact_name
        if PurePath(name).suffix.lower() not in SUPPORTED_EXT:
            return {"status": "unsupported",
                    "message": f"Format '{name}' belum didukung. Gunakan: {', '.join(sorted(SUPPORTED_EXT))}"}
        part = await ctx.load_artifact(name)
        if part is None or not part.inline_data:
            return {"status": "error",
                    "message": "File belum dilampirkan. Lampirkan file di chat (ikon klip) lalu ulangi /upload."}
        return {"status": "success", "artifact_name": name, "dataset": node_input.dataset,
                "create_new": node_input.create_new}

    async def upload(ctx: Context, node_input: dict) -> dict:
        if node_input["status"] != "success":
            return node_input
        try:
            # strict: upload ke dataset yang salah merugikan, jadi hanya nama persis yang diterima
            ds, candidates = await asyncio.to_thread(resolve_one, backend, node_input["dataset"], "dataset", True)
            if ds is None and candidates and not node_input["create_new"]:
                out = clarify(node_input["dataset"], candidates)
                out["message"] += (f" Atau buat dataset baru '{node_input['dataset']}': ulangi dengan create_new=true "
                                   "setelah user mengonfirmasi.")
                return out
            if ds is None:
                created = await asyncio.to_thread(backend.ensure_dataset, node_input["dataset"].strip())
                ds_id, ds_name = created.id, created.name
            else:
                ds_id, ds_name = ds.id, ds.label
            part = await ctx.load_artifact(node_input["artifact_name"])
            doc = await asyncio.to_thread(backend.upload, ds_id, node_input["artifact_name"], part.inline_data.data)
        except BackendError as e:
            return error_dict(e)
        return {"status": "success", "dataset_id": ds_id, "dataset": ds_name, "doc_id": doc.id, "document": doc.name}

    async def start_parse(node_input: dict) -> dict:
        if node_input["status"] != "success":
            return node_input
        try:
            await asyncio.to_thread(backend.start_parse, node_input["dataset_id"], [node_input["doc_id"]])
        except BackendError as e:
            return error_dict(e)
        return node_input

    async def wait_parsed(node_input: dict) -> dict:
        if node_input["status"] != "success":
            return node_input
        deadline = time.monotonic() + timeout
        while True:
            try:
                status = (await asyncio.to_thread(
                    backend.parse_status, node_input["dataset_id"], [node_input["doc_id"]]
                ))[node_input["doc_id"]]
            except BackendError as e:
                return error_dict(e)
            if status in ("DONE", "FAIL") or time.monotonic() >= deadline:
                return {**node_input, "parse_status": status}
            await asyncio.sleep(poll_interval)

    def report(ctx: Context, node_input: dict) -> dict:
        if node_input["status"] != "success":
            return node_input
        status, doc, ds = node_input["parse_status"], node_input["document"], node_input["dataset"]
        ctx.state["last_uploaded"] = {"document": doc, "dataset": ds, "status": status}
        if status == "DONE":
            return {"status": "success", "document": doc, "dataset": ds, "parse_status": status,
                    "message": f"'{doc}' tersimpan di '{ds}' dan siap dibahas."}
        if status == "FAIL":
            return {"status": "error", "document": doc, "dataset": ds, "parse_status": status,
                    "message": f"'{doc}' terupload ke '{ds}' tetapi parsing gagal. Cek di UI backend."}
        return {"status": "success", "document": doc, "dataset": ds, "parse_status": status,
                "message": f"'{doc}' terupload ke '{ds}', parsing masih berjalan. Cek lagi dengan /dataset."}

    return Workflow(
        name="ingest_pipeline",
        description="Simpan file lampiran ke dataset RAG, parse, dan tunggu sampai siap dibahas.",
        edges=[("START", load_file, upload, start_parse, wait_parsed, report)],
        input_schema=IngestRequest,
    )
