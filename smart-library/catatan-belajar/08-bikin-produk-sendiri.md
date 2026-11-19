# 08 · Bikin produk sendiri dari starter kit ini

**Tujuan:** memakai ulang Smart Library untuk domain lain, menambah backend, dan tahu jalur menuju produksi.

## 1. Ganti domain (tanpa menyentuh Python)

Contoh: chatbot SOP internal tim HR.

1. **Koleksi:** ubah `data/sources.yaml`, yaitu nama dataset dan daftar dokumen (url, filename, format). Untuk file lokal, taruh langsung di `data/downloads/` dengan nama yang sama.
2. **Persona:** edit `src/smart_library/prompts/*.md`. Ganti "Pustakawan" menjadi "Asisten SOP", sesuaikan contoh shortcut dan aturan jawaban (misalnya selalu menyebut nomor SOP).
3. **LightRAG:** ubah `LIGHTRAG_WORKSPACES` di `.env` (satu dataset = satu port).
4. Jalankan `uv run seed --backend all` lalu `uv run adk web agents`.
5. Tulis ulang `eval/questions.yaml` dengan pertanyaan nyata dari user domain itu.

## 2. Tambah backend baru (misal Qdrant, Vertex AI Search)

Cukup **satu file** di `src/smart_library/backends/`, yang mengimplementasikan 7 method `RagBackend` ([`base.py:41`](../src/smart_library/backends/base.py)):

```python
class QdrantBackend:
    name = "qdrant"
    def list_datasets(self): ...          # koleksi Qdrant
    def list_documents(self, dataset_id): ...
    def ensure_dataset(self, name, description=""): ...
    def upload(self, dataset_id, filename, data): ...   # parse + chunk + embed sendiri
    def start_parse(self, dataset_id, doc_ids): ...
    def parse_status(self, dataset_id, doc_ids): ...
    def retrieve(self, query, *, dataset_ids=None, document_ids=None, top_k=8): ...
```

Lalu:
1. Buat `agents/library_qdrant/agent.py` dengan isi `app = build_app(QdrantBackend.from_env())`.
2. Tulis `tests/integration/test_qdrant_backend.py` dengan meniru test RAGFlow/LightRAG.
3. Tambahkan `"qdrant"` di `factories` pada `cli/eval.py`, sehingga perbandingan tiga backend langsung jalan.

Agent, tools, workflow, persona, dan eval **tidak berubah sama sekali**. Itulah gunanya interface.

## 3. Ganti model LLM

Ubah `LLM_MODEL` di `.env` (format LiteLLM): `openai/gpt-4.1-mini` (deployment Azure lain), `gemini/gemini-2.5-flash`, `anthropic/claude-...`. Satu tempat: `config.make_model`.

## 4. Dari `adk web` ke produksi

| Tahap | Cara | Catatan |
|---|---|---|
| API lokal | `uv run adk api_server agents` | REST + SSE, dipakai frontend sendiri |
| FastAPI sendiri | `from google.adk.cli.fast_api import get_fast_api_app` | Tambah auth, CORS, logging |
| **Google Cloud (M6, berikutnya)** | Vertex AI **Agent Engine** atau **Cloud Run** (`adk deploy cloud_run` / `adk deploy agent_engine`) | Lihat PRD §9 M6. Yang perlu dipikirkan: RAGFlow & LightRAG juga harus bisa diakses dari cloud (VM/Cloud Run terpisah), secret di Secret Manager, dan session service persisten (Vertex/DB) menggantikan in-memory |

Checklist sebelum produksi:
- [ ] Session & artifact service persisten (bukan in-memory)
- [ ] Auth user + pembatasan dataset per user
- [ ] Rahasia di secret manager, bukan `.env`
- [ ] Observability (OpenTelemetry sudah ada di ADK)
- [ ] `adk eval` dijalankan di CI pada setiap PR
