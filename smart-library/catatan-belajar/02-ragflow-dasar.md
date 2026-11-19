# 02 · RAGFlow: dataset, dokumen, parsing, retrieval

**Tujuan:** memahami alur kerja RAGFlow dan memakainya dari Python, persis seperti yang dilakukan [`ragflow_backend.py`](../src/smart_library/backends/ragflow_backend.py).

## Konsep

```
 upload file ──▶ Dataset ──▶ Parsing (DeepDoc) ──▶ Chunking ──▶ Embedding ──▶ Index (Elasticsearch/Infinity)
                                                                                   │
 pertanyaan ──▶ embedding pertanyaan ──▶ hybrid search (vektor + kata kunci) ──▶ (rerank) ──▶ chunk + skor
```

| Istilah RAGFlow | Artinya | Di kode kita |
|---|---|---|
| **Dataset** (dulu "knowledge base") | Wadah dokumen dengan satu model embedding & metode chunking | `Dataset` di `backends/base.py:8` |
| **Document** | File yang diupload ke dataset | `Document` (`base.py:16`) |
| **Parsing** | DeepDoc membaca layout (judul, tabel, gambar, OCR), lalu memotong jadi chunk | `start_parse` → `async_parse_documents` |
| **Chunk** | Potongan teks + posisi halaman + skor kemiripan | `Chunk` (`base.py:24`) |
| **Retrieval** | Hybrid search: `vector_similarity_weight` mengatur porsi vektor vs kata kunci | `retrieve` (`ragflow_backend.py:135`) |
| **Chat assistant** | Fitur chat bawaan RAGFlow | **Tidak dipakai.** Jawaban ditulis agent ADK supaya adil dibanding LightRAG |

**Kenapa RAGFlow menonjol:** DeepDoc memahami *layout* dokumen (tabel, kolom, header). Konsekuensinya, parsing di CPU lambat. Di laptop, PDF 180 halaman (Stranas KA) butuh puluhan menit.

## Kode kita

```python
from ragflow_sdk import RAGFlow
rag = RAGFlow(api_key=..., base_url="http://localhost")

ds = rag.list_datasets(name="Riset RAG")[0]
docs = ds.list_documents(page=1, page_size=100)    # server membatasi page_size <= 100
ds.upload_documents([{"display_name": "a.pdf", "blob": data}])
ds.async_parse_documents([doc_id])                 # parsing berjalan di background

chunks = rag.retrieve(dataset_ids=[ds.id], document_ids=None,
                      question="apa itu RAG", page_size=8, similarity_threshold=0.2)
for c in chunks:
    print(c.document_name, c.similarity, c.positions[0][0], c.content[:80])  # positions[0][0] = halaman
```

### Hal yang hanya ketahuan saat mencoba (server v1.0 + SDK 0.26)

Ketiganya ditangani di `ragflow_backend.py` dan diberi komentar `shortcut:`:

1. `create_dataset` dari SDK mengirim `avatar`/`description`/`chunk_method`, yang **ditolak** server v1.0. Kita memakai `POST /datasets` langsung dengan `name`, `parser_id`, `parse_type`, `embedding_model`, lalu mengisi description lewat `update`.
2. `list_documents(name=...)` untuk nama yang **belum ada** mengembalikan error, bukan list kosong. Karena itu dokumen dicocokkan sendiri lewat helper `_all_docs`.
3. Field `run` dokumen bisa tetap `"0"` walau parsing selesai. Status dihitung dari `run` **dan** `progress` (`map_status`, `ragflow_backend.py:12`).

**Pelajaran:** selalu tulis *integration test* ke server asli ([`tests/integration/test_ragflow_backend.py`](../tests/integration/test_ragflow_backend.py)). Mock tidak akan menemukan ketiga hal di atas.

## Coba sendiri

1. Buka UI RAGFlow → dataset **Riset RAG** → klik satu dokumen → lihat chunk hasil DeepDoc (perhatikan tabel yang tetap utuh).
2. Menu **Retrieval testing** di dataset: tanyakan "dual-level retrieval". Bandingkan dengan:
   ```powershell
   uv run python -c "from smart_library.backends.ragflow_backend import RagflowBackend as R; [print(c.score, c.document, c.location) for c in R.from_env().retrieve('dual-level retrieval')]"
   ```
   Hasilnya seharusnya mirip, karena sama-sama hybrid search.
3. Ubah `similarity_threshold` di `retrieve` menjadi `0.5`. Apa yang terjadi pada jumlah chunk?

## Kesalahan umum

| Gejala | Solusi |
|---|---|
| `extra inputs are not permitted: ...` | Field tidak diterima server v1.0. Cek `internal/handler/dataset.go` di repo ragflow untuk daftar field yang valid |
| `page_size must be between 1 and 100` | Pakai paginasi (`_all_docs`) |
| Retrieval kosong | Dokumen belum DONE (`/dataset` di chat) atau threshold terlalu tinggi |
