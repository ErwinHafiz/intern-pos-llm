"""Kontrak backend RAG. Tidak boleh import google.adk: backend bisa dipakai di luar ADK."""

from dataclasses import dataclass
from typing import Protocol


@dataclass
class Dataset:
    id: str
    name: str
    description: str = ""
    doc_count: int = 0


@dataclass
class Document:
    id: str
    name: str
    dataset_id: str
    status: str  # DONE | RUNNING | FAIL | PENDING


@dataclass
class Chunk:
    text: str
    document: str
    dataset: str
    score: float
    location: str | None = None
    kind: str = "chunk"  # chunk | entity | relation


class BackendError(Exception):
    """Pesan sudah siap ditampilkan ke user (bahasa Indonesia)."""


class Unsupported(BackendError):
    """Fitur tidak didukung oleh backend ini."""


class RagBackend(Protocol):
    name: str

    def list_datasets(self) -> list[Dataset]: ...
    def list_documents(self, dataset_id: str) -> list[Document]: ...
    def ensure_dataset(self, name: str, description: str = "") -> Dataset: ...
    def upload(self, dataset_id: str, filename: str, data: bytes) -> Document: ...
    def start_parse(self, dataset_id: str, doc_ids: list[str]) -> None: ...
    def parse_status(self, dataset_id: str, doc_ids: list[str]) -> dict[str, str]: ...
    def retrieve(
        self,
        query: str,
        *,
        dataset_ids: list[str] | None = None,
        document_ids: list[str] | None = None,
        top_k: int = 8,
    ) -> list[Chunk]: ...


def find_dataset(backend: RagBackend, name: str) -> Dataset:
    datasets = backend.list_datasets()
    for ds in datasets:
        if ds.name.lower() == name.strip().lower():
            return ds
    available = ", ".join(d.name for d in datasets) or "(belum ada)"
    raise BackendError(f"Dataset '{name}' tidak ditemukan. Tersedia: {available}")
