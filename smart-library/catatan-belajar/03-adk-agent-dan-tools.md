# 03 · ADK: LlmAgent, function tool, ToolContext, state

**Tujuan:** paham bagaimana satu agent memakai tools, dan bagaimana tools berbagi data lewat `session.state`.

## Konsep

```
            ┌─────────────── LlmAgent ───────────────┐
 user ──▶   │ instruction (persona .md)               │
            │ model (LiteLlm → Azure gpt-5.1)         │ ──▶ LLM memutuskan memanggil tool
            │ tools = [search, read_document, ...]    │ ◀── hasil tool (dict ber-"status")
            └──────────────────────────────────────────┘
                       │ tool_context.state["scope"] = {...}   (tersimpan di sesi)
```

- **Function tool** = fungsi Python biasa. ADK membaca **nama, type hint, dan docstring** untuk membuat deskripsi tool bagi LLM. Docstring yang baik = tool dipakai dengan benar.
- **`tool_context: ToolContext`** = parameter khusus yang disuntik ADK dan **tidak terlihat oleh LLM**. Dipakai untuk membaca/menulis `state`, artifact, dan lainnya.
- **Konvensi hasil:** selalu kembalikan `dict` dengan `"status"` (`success` / `error` / `unsupported` / `needs_clarification`). LLM jadi tahu harus menjawab, meminta maaf, atau bertanya balik.

## Kode kita

**Pola factory + closure** ([`tools/research_tools.py:12`](../src/smart_library/tools/research_tools.py)): backend di-*inject* tanpa terlihat oleh LLM.

```python
def make_research_tools(backend: RagBackend, top_k: int = 8) -> list:
    def search(query: str, tool_context: ToolContext) -> dict:
        """Cari potongan dokumen yang relevan dengan pertanyaan, di dalam scope aktif.

        Args:
            query: Pertanyaan atau kata kunci pencarian.
        """
        scope = tool_context.state.get("scope") or {}
        chunks = backend.retrieve(query, dataset_ids=scope.get("datasets") or None, ...)
        return {"status": "success", "sources": chunks_to_sources(chunks)}
    return [search, read_document]
```

Cek deklarasi yang dilihat LLM (perhatikan bahwa `tool_context` tidak muncul):

```powershell
uv run python -c "from google.adk.tools import FunctionTool; from smart_library.tools.catalog_tools import make_catalog_tools; from smart_library.backends.ragflow_backend import RagflowBackend as R; print(FunctionTool(make_catalog_tools(R.from_env())[2])._get_declaration().model_dump(exclude_none=True))"
```

**State sebagai memori bersama.** `set_scope` (`catalog_tools.py:42`) dan `read_document` menulis `state["scope"]`, lalu `search` membacanya. Karena itu pertanyaan lanjutan setelah `/bahas X` otomatis mencari di dokumen X. Lihat nilainya di tab **State** pada `adk web`.

**Model lewat LiteLLM** ([`config.py:53`](../src/smart_library/config.py)): `LiteLlm(model="openai/gpt-5.1", api_base=".../openai/v1", api_key=...)`. Endpoint Azure `/openai/v1` kompatibel OpenAI, jadi prefix-nya `openai/`.

**Nama longgar → dokumen asli** ([`naming.py`](../src/smart_library/naming.py)): user menulis "uu pdp", sementara nama file aslinya "UU Nomor 27 Tahun 2022 tentang Pelindungan Data Pribadi.pdf". Resolver mencoba kecocokan persis → substring per kata utuh → singkatan (pelindungan data pribadi = *pdp*) → typo. Kalau ambigu (termasuk dua kandidat yang sama mirip), tool mengembalikan `needs_clarification` + kandidat, bukan menebak. Untuk **upload**, nama dataset harus sama persis (`strict=True`): "Riset LLM" tidak boleh diam-diam masuk ke "Riset RAG". User ditanya dulu, lalu dataset baru dibuat dengan `create_new=true`.

## Coba sendiri

1. Tambahkan tool `count_documents(dataset: str) -> dict` di `catalog_tools.py`. Daftarkan di list return, lalu tanyakan "berapa dokumen di Riset RAG?" di `adk web`. Lihat di tab Trace apakah LLM memilih tool barumu.
2. Hapus docstring `search` lalu jalankan lagi. Bagaimana perilaku LLM berubah?
3. Tulis unit test untuk tool barumu dengan `FakeBackend` (contoh: [`tests/unit/test_tools.py`](../tests/unit/test_tools.py)).

## Kesalahan umum

| Gejala | Solusi |
|---|---|
| `non-default argument follows default argument` | Taruh `tool_context` sebelum parameter ber-default, atau beri default ke semua parameter sesudahnya |
| LLM tidak memanggil tool | Docstring kurang jelas, atau persona tidak menyebut kapan tool dipakai |
| Tool melempar exception → chat error | Tangkap `BackendError`, kembalikan `error_dict(e)` |
| Kurung kurawal `{x}` di instruction hilang/aneh | ADK menganggap `{x}` sebagai placeholder state. Hindari `{}` di file persona (ada test-nya) |
