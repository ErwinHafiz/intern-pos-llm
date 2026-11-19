"""Tools untuk research_agent: cari & baca isi dokumen (selalu dengan sumber bernomor)."""

from google.adk.tools import ToolContext

from smart_library.backends.base import BackendError, RagBackend
from smart_library.naming import resolve_one
from smart_library.tools.formatting import chunks_to_sources, clarify, error_dict

NOT_FOUND = "Informasi tidak ditemukan di sumber. Jangan mengarang; sampaikan ke user apa adanya."


def make_research_tools(backend: RagBackend, top_k: int = 8) -> list:
    def search(query: str, tool_context: ToolContext) -> dict:
        """Cari potongan dokumen yang relevan dengan pertanyaan, di dalam scope aktif.

        Args:
            query: Pertanyaan atau kata kunci pencarian.
        """
        scope = tool_context.state.get("scope") or {}
        try:
            chunks = backend.retrieve(
                query, dataset_ids=scope.get("datasets") or None,
                document_ids=scope.get("documents") or None, top_k=top_k,
            )
        except BackendError as e:
            return error_dict(e)
        out = {"status": "success", "scope": scope.get("label", "semua dataset"), "sources": chunks_to_sources(chunks)}
        if not chunks:
            out["message"] = NOT_FOUND
        return out

    def read_document(document: str, tool_context: ToolContext, focus: str = "") -> dict:
        """Ambil potongan-potongan utama satu dokumen untuk diringkas atau dibahas.
        Sekaligus mengunci scope ke dokumen ini, jadi `search` berikutnya mencari di dokumen yang sama.

        Args:
            document: Nama dokumen, boleh tidak persis (mis. "uu pdp", "paper lightrag").
            focus: Aspek yang ingin dibahas (opsional). Kosong = ringkasan umum.
        """
        try:
            doc, candidates = resolve_one(backend, document, kind="document")
            if doc is None:
                return clarify(document, candidates)
            chunks = backend.retrieve(
                focus or "ringkasan isi utama, tujuan, ruang lingkup, poin penting",
                dataset_ids=[doc.dataset_id], document_ids=[doc.id], top_k=12,
            )
        except BackendError as e:
            return error_dict(e)
        tool_context.state["scope"] = {"datasets": [doc.dataset_id], "documents": [doc.id], "label": doc.label}
        out = {"status": "success", "document": doc.label, "sources": chunks_to_sources(chunks)}
        if not chunks:
            out["message"] = NOT_FOUND
        return out

    return [search, read_document]
