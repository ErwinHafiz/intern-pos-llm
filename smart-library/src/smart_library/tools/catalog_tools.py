"""Tools untuk catalog_agent: lihat koleksi & tentukan scope aktif.

Pola factory: backend di-inject lewat closure, jadi ADK hanya melihat parameter
yang relevan untuk LLM (nama + docstring = deskripsi tool).
"""

from google.adk.tools import ToolContext

from smart_library.backends.base import BackendError, RagBackend
from smart_library.naming import resolve_one
from smart_library.tools.formatting import clarify, error_dict


def make_catalog_tools(backend: RagBackend) -> list:
    def list_datasets() -> dict:
        """Daftar semua dataset (koleksi dokumen) beserta jumlah dokumennya."""
        try:
            datasets = backend.list_datasets()
        except BackendError as e:
            return error_dict(e)
        return {
            "status": "success",
            "datasets": [{"name": d.name, "description": d.description, "documents": d.doc_count} for d in datasets],
        }

    def list_documents(dataset: str) -> dict:
        """Daftar dokumen dalam satu dataset beserta status parsing (DONE/RUNNING/FAIL/PENDING).

        Args:
            dataset: Nama dataset, boleh tidak persis (mis. "riset rag").
        """
        try:
            ds, candidates = resolve_one(backend, dataset, kind="dataset")
            if ds is None:
                return clarify(dataset, candidates)
            docs = backend.list_documents(ds.id)
        except BackendError as e:
            return error_dict(e)
        return {"status": "success", "dataset": ds.label,
                "documents": [{"name": d.name, "status": d.status} for d in docs]}

    def set_scope(tool_context: ToolContext, dataset: str = "", document: str = "") -> dict:
        """Tetapkan fokus percakapan ke satu dataset ATAU satu dokumen. Tanpa argumen = semua dataset.

        Args:
            dataset: Nama dataset yang jadi fokus (opsional).
            document: Nama dokumen yang jadi fokus (opsional, diutamakan bila keduanya diisi).
        """
        if not (dataset or document):
            tool_context.state["scope"] = {}
            return {"status": "success", "scope": "semua dataset"}
        name, kind = (document, "document") if document else (dataset, "dataset")
        try:
            target, candidates = resolve_one(backend, name, kind=kind)
        except BackendError as e:
            return error_dict(e)
        if target is None:
            return clarify(name, candidates)
        tool_context.state["scope"] = {
            "datasets": [target.dataset_id],
            "documents": [target.id] if kind == "document" else [],
            "label": target.label,
        }
        return {"status": "success", "scope": target.label, "kind": kind}

    return [list_datasets, list_documents, set_scope]
