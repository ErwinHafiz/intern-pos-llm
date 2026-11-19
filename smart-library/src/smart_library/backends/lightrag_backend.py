"""Adapter LightRAG Server (REST). 1 dataset = 1 server/workspace (lihat cli/lightrag_up.py).

Hanya retrieval (`/query/data`); jawaban ditulis agent ADK, sama seperti RAGFlow.
Selain potongan teks, LightRAG mengembalikan entitas & relasi dari knowledge graph:
dipetakan ke Chunk.kind = "entity" / "relation".
"""

import functools
import math
from collections.abc import Callable
from pathlib import PurePath

import httpx

from smart_library.backends.base import BackendError, Chunk, Dataset, Document, Unsupported

_RUNNING = {"processing", "parsing", "analyzing", "preprocessed"}
SEP = "<SEP>"  # LightRAG menggabungkan beberapa file_path dengan pemisah ini


def map_doc_status(raw: str) -> str:
    s = str(raw).lower().removeprefix("docstatus.")
    if s == "processed":
        return "DONE"
    if s == "failed":
        return "FAIL"
    return "RUNNING" if s in _RUNNING else "PENDING"


def _doc_name(file_path: str) -> str:
    return SEP.join(PurePath(p).name for p in str(file_path).split(SEP))


def query_data_to_chunks(payload: dict, dataset: str, top_k: int = 8) -> list[Chunk]:
    """chunks dulu (bukti utama), lalu entitas & relasi graph. Skor = urutan (API tidak memberi skor)."""
    data = payload.get("data") or {}
    items = [("chunk", c["content"], c.get("file_path", "")) for c in data.get("chunks", [])[:top_k]]
    items += [("entity", f"{e['entity_name']}: {e.get('description', '')}", e.get("file_path", ""))
              for e in data.get("entities", [])[: max(1, top_k // 2)]]
    items += [("relation", f"{r['src_id']} → {r['tgt_id']}: {r.get('description', '')}", r.get("file_path", ""))
              for r in data.get("relationships", [])[: max(1, top_k // 2)]]
    n = len(items)
    return [Chunk(text, _doc_name(fp), dataset, round(1 - i / (n + 1), 4), None, kind)
            for i, (kind, text, fp) in enumerate(items)]


def filter_by_documents(chunks: list[Chunk], names: set[str]) -> list[Chunk]:
    """shortcut: filter per dokumen dilakukan SETELAH retrieval (LightRAG tidak punya filter dokumen),
    jadi hasil bisa lebih sedikit dari top_k. Perbesar top_k bila perlu."""
    kept = []
    for c in chunks:
        hit = [n for n in c.document.split(SEP) if n in names]
        if hit:
            c.document = hit[0]
            kept.append(c)
    return kept


def _errors(fn):
    @functools.wraps(fn)
    def wrapper(self, *args, **kwargs):
        try:
            return fn(self, *args, **kwargs)
        except BackendError:
            raise
        except httpx.TransportError as e:
            raise BackendError(
                f"LightRAG Server tidak aktif ({e.request.url.host}:{e.request.url.port}). "
                "Jalankan `uv run lightrag-up`."
            ) from e
        except httpx.HTTPStatusError as e:
            raise BackendError(f"LightRAG error {e.response.status_code}: {e.response.text[:200]}") from e
        except (ValueError, KeyError) as e:  # body non-JSON atau field hilang: jangan sampai jadi traceback
            raise BackendError(f"LightRAG memberi respons tidak terduga ({type(e).__name__}: {e}). Cek log di data/lightrag/logs/") from e

    return wrapper


class LightragBackend:
    name = "lightrag"

    def __init__(self, workspaces: dict[str, str], api_key: str = "", timeout: float = 120,
                 embed: Callable[[list[str]], list[list[float]]] | None = None):
        headers = {"X-API-Key": api_key} if api_key else {}
        self.clients = {name: httpx.Client(base_url=url, headers=headers, timeout=timeout)
                        for name, url in workspaces.items()}
        # LightRAG tidak memberi skor relevansi; untuk menggabungkan hasil beberapa server
        # (dataset) kita rerank dengan embedding yang sama dengan yang dipakai indexing.
        self.embed = embed

    @classmethod
    def from_env(cls) -> "LightragBackend":
        from smart_library.config import load_settings

        s = load_settings()
        if not s.lightrag_workspaces:
            raise BackendError("LIGHTRAG_WORKSPACES kosong di .env")

        def embed(texts: list[str]) -> list[list[float]]:
            r = httpx.post(f"{s.llm_api_base}/embeddings", headers={"api-key": s.llm_api_key},
                           json={"model": s.embedding_deployment, "input": [t[:8000] for t in texts]}, timeout=60)
            r.raise_for_status()
            return [d["embedding"] for d in sorted(r.json()["data"], key=lambda d: d["index"])]

        return cls(s.lightrag_workspaces, s.lightrag_api_key, embed=embed)

    def _client(self, dataset_id: str) -> httpx.Client:
        if dataset_id not in self.clients:
            raise BackendError(f"Dataset '{dataset_id}' tidak ada di LIGHTRAG_WORKSPACES")
        return self.clients[dataset_id]

    def _docs(self, dataset_id: str) -> list[dict]:
        out, page = [], 1
        while True:
            r = self._client(dataset_id).post("/documents/paginated", json={"page": page, "page_size": 100})
            r.raise_for_status()
            batch = r.json().get("documents", [])
            out += batch
            if len(batch) < 100:
                return out
            page += 1

    @_errors
    def list_datasets(self) -> list[Dataset]:
        return [Dataset(name, name, "", len(self._docs(name))) for name in self.clients]

    @_errors
    def list_documents(self, dataset_id: str) -> list[Document]:
        return [Document(d["id"], _doc_name(d["file_path"]), dataset_id, map_doc_status(d["status"]))
                for d in self._docs(dataset_id)]

    def ensure_dataset(self, name: str, description: str = "") -> Dataset:
        for ds in self.clients:
            if ds.lower() == name.strip().lower():
                return Dataset(ds, ds, description)
        raise Unsupported(
            f"Dataset baru '{name}' di LightRAG perlu server baru: tambahkan ke LIGHTRAG_WORKSPACES "
            "di .env lalu jalankan ulang `uv run lightrag-up`."
        )

    @_errors
    def upload(self, dataset_id: str, filename: str, data: bytes) -> Document:
        if any(_doc_name(d["file_path"]) == filename for d in self._docs(dataset_id)):
            raise BackendError(f"'{filename}' sudah ada di dataset '{dataset_id}'. Tidak diupload ulang.")
        r = self._client(dataset_id).post("/documents/upload", files={"file": (filename, data)})
        r.raise_for_status()
        body = r.json()
        if body.get("status") == "duplicated":
            raise BackendError(f"'{filename}' sudah ada di dataset '{dataset_id}'. Tidak diupload ulang.")
        if body.get("status") == "failure":
            raise BackendError(f"LightRAG menolak '{filename}': {body.get('message')}")
        # id dokumen baru diketahui setelah diproses; pakai track_id untuk memantau status
        return Document(body["track_id"], filename, dataset_id, "PENDING")

    def start_parse(self, dataset_id: str, doc_ids: list[str]) -> None:
        """LightRAG memproses otomatis setelah upload."""

    @_errors
    def parse_status(self, dataset_id: str, doc_ids: list[str]) -> dict[str, str]:
        out, listing = {}, None
        for doc_id in doc_ids:
            if doc_id.startswith("upload_"):  # track_id dari upload
                r = self._client(dataset_id).get(f"/documents/track_status/{doc_id}")
                r.raise_for_status()
                statuses = [map_doc_status(d["status"]) for d in r.json().get("documents", [])]
                out[doc_id] = ("FAIL" if "FAIL" in statuses else "DONE" if statuses and set(statuses) == {"DONE"}
                               else "RUNNING" if statuses else "PENDING")
            else:
                listing = listing or {d["id"]: map_doc_status(d["status"]) for d in self._docs(dataset_id)}
                out[doc_id] = listing.get(doc_id, "PENDING")
        return out

    @_errors
    def retrieve(self, query, *, dataset_ids=None, document_ids=None, top_k=8) -> list[Chunk]:
        chunks: list[Chunk] = []
        for ds in dataset_ids or list(self.clients):
            # filter dokumen baru dilakukan sesudah retrieval, jadi ambil lebih banyak agar dokumen target ikut
            wide = top_k * 3 if document_ids else top_k
            r = self._client(ds).post("/query/data", json={
                "query": query, "mode": "mix", "top_k": wide * 2, "chunk_top_k": wide,
            })
            r.raise_for_status()
            found = query_data_to_chunks(r.json(), ds, wide)
            if document_ids:
                names = {_doc_name(d["file_path"]) for d in self._docs(ds) if d["id"] in document_ids}
                found = filter_by_documents(found, names)
            chunks += found
        if self.embed and len(dataset_ids or self.clients) > 1 and chunks:
            chunks = self._rerank(query, chunks, top_k)
        return sorted(chunks, key=lambda c: (c.kind != "chunk", -c.score))

    def _rerank(self, query: str, chunks: list[Chunk], top_k: int) -> list[Chunk]:
        try:
            vecs = self.embed([query] + [c.text for c in chunks])
        except (httpx.HTTPError, ValueError, KeyError) as e:
            raise BackendError(f"Embedding Azure gagal saat menggabungkan hasil antar-dataset ({type(e).__name__}). "
                               "Cek LLM_API_BASE/EMBEDDING_DEPLOYMENT di .env atau koneksi ke Azure.") from e
        q = vecs[0]
        for c, v in zip(chunks, vecs[1:]):
            dot = sum(a * b for a, b in zip(q, v))
            c.score = round(dot / ((math.sqrt(sum(a * a for a in q)) * math.sqrt(sum(b * b for b in v))) or 1), 4)
        ranked = sorted(chunks, key=lambda c: -c.score)
        limits = {"chunk": top_k, "entity": max(1, top_k // 2), "relation": max(1, top_k // 2)}
        kept, count = [], {k: 0 for k in limits}
        for c in ranked:
            if count[c.kind] < limits[c.kind]:
                kept.append(c)
                count[c.kind] += 1
        return kept
