"""Adapter RAGFlow (lewat ragflow-sdk). Hanya retrieval; jawaban ditulis agent ADK."""

import functools

from ragflow_sdk import RAGFlow

from smart_library.backends.base import BackendError, Chunk, Dataset, Document

_DONE, _RUNNING, _FAIL = {"DONE", "3"}, {"RUNNING", "1"}, {"FAIL", "4", "CANCEL", "2"}


def map_status(run: str, progress: float) -> str:
    """Status RAGFlow -> DONE/RUNNING/FAIL/PENDING.

    Server v1.0 kadang tetap mengirim run="0" untuk dokumen yang sudah selesai,
    jadi `progress` ikut dipakai (1 = selesai, -1 = gagal).
    """
    run = str(run).upper()
    if run in _FAIL or progress < 0:
        return "FAIL"
    if run in _DONE or progress >= 1:
        return "DONE"
    if run in _RUNNING or progress > 0:
        return "RUNNING"
    return "PENDING"


def chunk_location(positions) -> str | None:
    """positions RAGFlow = [[halaman, x0, x1, top, bottom], ...]"""
    return f"hlm. {positions[0][0]}" if positions else None


def _all_docs(ds) -> list:
    """Semua dokumen di dataset (server membatasi page_size <= 100)."""
    out, page = [], 1
    while batch := ds.list_documents(page=page, page_size=100):
        out += batch
        if len(batch) < 100:
            break
        page += 1
    return out


def _errors(fn):
    """Ubah error SDK/jaringan jadi BackendError dengan pesan yang bisa ditindaklanjuti."""

    @functools.wraps(fn)
    def wrapper(self, *args, **kwargs):
        try:
            return fn(self, *args, **kwargs)
        except BackendError:
            raise
        except ValueError as e:  # termasuk requests.JSONDecodeError: server hidup tapi membalas non-JSON
            raise BackendError(
                f"RAGFlow di {self.base_url} memberi respons tidak valid (server sibuk/restart atau Docker bermasalah). "
                "Cek `docker ps` lalu coba lagi."
            ) from e
        except OSError as e:  # requests.ConnectionError turunan OSError
            raise BackendError(
                f"RAGFlow tidak bisa dihubungi di {self.base_url}. Jalankan `docker compose up -d` "
                f"di folder ragflow/docker ({type(e).__name__})"
            ) from e
        except Exception as e:  # SDK melempar Exception(message) untuk error API
            raise BackendError(f"RAGFlow error: {e}") from e

    return wrapper


class RagflowBackend:
    name = "ragflow"

    def __init__(self, base_url: str, api_key: str, embedding_model: str = ""):
        self.base_url = base_url
        self.embedding_model = embedding_model or None
        self.rag = RAGFlow(api_key=api_key, base_url=base_url)

    @classmethod
    def from_env(cls) -> "RagflowBackend":
        from smart_library.config import load_settings

        s = load_settings()
        return cls(s.ragflow_base_url, s.ragflow_api_key, s.ragflow_embedding_model)

    def _ds(self, dataset_id: str):
        found = self.rag.list_datasets(id=dataset_id)
        if not found:
            raise BackendError(f"Dataset dengan id {dataset_id} tidak ada di RAGFlow")
        return found[0]

    @_errors
    def list_datasets(self) -> list[Dataset]:
        return [
            Dataset(d.id, d.name, d.description or "", d.document_count)
            for d in self.rag.list_datasets(page_size=100)
        ]

    @_errors
    def list_documents(self, dataset_id: str) -> list[Document]:
        docs = _all_docs(self._ds(dataset_id))
        return [Document(d.id, d.name, dataset_id, map_status(d.run, d.progress)) for d in docs]

    @_errors
    def ensure_dataset(self, name: str, description: str = "") -> Dataset:
        for d in self.rag.list_datasets(name=name):
            if d.name == name:
                return Dataset(d.id, d.name, d.description or "", d.document_count)
        # shortcut: SDK 0.26 create_dataset mengirim avatar/description/chunk_method yang ditolak
        # server v1.0 (POST hanya terima name, embedding_model, parser_id, ...). Description
        # diisi lewat update. Kembali ke rag.create_dataset bila SDK sudah sinkron dengan server.
        payload = {"name": name, "parser_id": "naive", "parse_type": 1}  # 1 = parser bawaan
        if self.embedding_model:
            payload["embedding_model"] = self.embedding_model
        res = self.rag.post("/datasets", payload).json()
        if res.get("code") != 0:
            raise BackendError(f"RAGFlow gagal membuat dataset '{name}': {res.get('message')}")
        ds_id = res["data"]["id"]
        if description:
            self._ds(ds_id).update({"description": description})
        return Dataset(ds_id, name, description, 0)

    @_errors
    def upload(self, dataset_id: str, filename: str, data: bytes) -> Document:
        ds = self._ds(dataset_id)
        # filter name= di server v1.0 error bila nama belum ada, jadi cocokkan sendiri
        if any(d.name == filename for d in _all_docs(ds)):
            raise BackendError(f"'{filename}' sudah ada di dataset '{ds.name}'. Tidak diupload ulang.")
        doc = ds.upload_documents([{"display_name": filename, "blob": data}])[0]
        return Document(doc.id, doc.name, dataset_id, "PENDING")

    @_errors
    def start_parse(self, dataset_id: str, doc_ids: list[str]) -> None:
        self._ds(dataset_id).async_parse_documents(doc_ids)

    @_errors
    def parse_status(self, dataset_id: str, doc_ids: list[str]) -> dict[str, str]:
        ds = self._ds(dataset_id)
        return {i: map_status(d.run, d.progress) for i in doc_ids for d in ds.list_documents(id=i)}

    @_errors
    def retrieve(self, query, *, dataset_ids=None, document_ids=None, top_k=8) -> list[Chunk]:
        names = {d.id: d.name for d in self.rag.list_datasets(page_size=100)}
        ids = dataset_ids or list(names)
        if not ids:
            return []
        chunks = self.rag.retrieve(
            dataset_ids=ids, document_ids=document_ids, question=query,
            page_size=top_k, similarity_threshold=0.2,
        )
        return [
            Chunk(c.content, c.document_name, names.get(c.dataset_id, ""), c.similarity, chunk_location(c.positions))
            for c in chunks
        ]
