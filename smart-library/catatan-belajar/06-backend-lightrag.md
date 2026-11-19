# 06 · Interface backend & LightRAG

**Tujuan:** paham kenapa ada interface `RagBackend`, cara kerja adapter LightRAG, dan apa beda nyata RAGFlow dan LightRAG di project ini.

## Interface = kontrak

[`backends/base.py:41`](../src/smart_library/backends/base.py) mendefinisikan 7 method. Tools, workflow, dan agent **hanya** mengenal interface ini:

```
tools/ & workflows/  ──▶  RagBackend (Protocol)  ◀── RagflowBackend   (ragflow-sdk)
                                                 ◀── LightragBackend  (REST LightRAG Server)
                                                 ◀── FakeBackend      (tests/unit saja)
```

Aturan:
- `backends/` **tidak** meng-import ADK, sehingga bisa dipakai di skrip, notebook, atau framework lain.
- Semua error menjadi `BackendError` dengan pesan berbahasa Indonesia yang langsung bisa ditindaklanjuti. Fitur yang tidak didukung menjadi `Unsupported`.
- Agent identik untuk kedua backend: `agents/library_ragflow/agent.py` dan `agents/library_lightrag/agent.py` hanya berbeda satu baris.

## Cara kerja LightRAG

```
upload ──▶ parse (legacy: pypdf/python-docx/…) ──▶ chunk ──▶ LLM ekstraksi entitas & relasi ──▶ knowledge graph
                                                         └──▶ embedding chunk/entitas/relasi ──▶ vector DB
query (mode "mix") ──▶ kata kunci low-level (entitas) + high-level (tema) ──▶ graph + vektor ──▶ chunks + entities + relationships
```

Kita memanggil `POST /query/data`, yang hanya mengembalikan konteks (tanpa jawaban LLM LightRAG). Hasilnya dipetakan oleh `query_data_to_chunks` ([`lightrag_backend.py:32`](../src/smart_library/backends/lightrag_backend.py)):

| Data LightRAG | `Chunk.kind` | Teks |
|---|---|---|
| `chunks[]` | `chunk` | isi potongan |
| `entities[]` | `entity` | `"<nama>: <deskripsi>"` |
| `relationships[]` | `relation` | `"<A> → <B>: <deskripsi>"` |

Persona `research.md` menyebut sumber `entity`/`relation` sebagai "graph pengetahuan".

## Satu dataset = satu server

LightRAG Server 1.5.7 menetapkan workspace saat start (header `LIGHTRAG-WORKSPACE` hanya dipakai `/health`). Karena itu `uv run lightrag-up` menjalankan satu proses per dataset:

| Dataset | Server | WebUI |
|---|---|---|
| Regulasi Digital ID | :9621 | http://localhost:9621/webui |
| Riset RAG | :9622 | http://localhost:9622/webui |

Konsekuensinya, membuat dataset baru dari chat (`/upload` ke dataset baru) mengembalikan `unsupported` dengan petunjuk menambah `LIGHTRAG_WORKSPACES`.

## Perbedaan nyata (hasil implementasi)

| Aspek | RAGFlow | LightRAG |
|---|---|---|
| Parsing | **DeepDoc**: layout, tabel, OCR. Akurat tapi lambat di CPU (puluhan menit per PDF besar) | Ekstraksi teks biasa. Cepat, tapi tabel/layout hilang |
| Biaya indexing | Tanpa LLM (hanya embedding) | **LLM per chunk** untuk ekstraksi graph (di sini `gpt-4.1-mini`) |
| Lokasi sumber | Nomor halaman (`positions`) | Hanya nama file |
| Skor relevansi | Ada (`similarity`) | Tidak ada, sehingga skor = urutan |
| Filter per dokumen | Native (`document_ids`) | Post-filter berdasarkan `file_path`, bisa < top_k |
| Banyak dataset | Native | Satu server per dataset |
| Konteks tambahan | — | Entitas & relasi graph, cocok untuk pertanyaan relasional/global |
| Status parsing | `run` + `progress` (`run` kadang tetap "0") | `processed/processing/…` via `track_status` |
| Ketahanan di laptop | Butuh Docker + Elasticsearch (RAM besar; ES sempat mati saat RAM sisa ±1 GB) | Proses Python ringan |

## Masalah nyata yang ditemui (dan perbaikannya)

1. `--input-dir` diberi `/<workspace>` lagi oleh server, sehingga path-nya ganda. **Fix:** kirim direktori dasar.
2. Parser mencari file sumber lewat **env `INPUT_DIR`**, bukan `--input-dir`, sehingga muncul `legacy source file not found`. **Fix:** `lightrag-up` men-set `INPUT_DIR`.
3. `GET /documents` mengembalikan 405. **Fix:** pakai `POST /documents/paginated`.
4. Upload tidak mengembalikan id dokumen. **Fix:** `Document.id` = `track_id`, lalu status dipantau lewat `/documents/track_status/{id}`.

5. **Hasil beberapa dataset digabung tanpa skor.** LightRAG tidak memberi skor relevansi, jadi saat mencari di semua dataset, chunk paper riset diselang-seling setara dengan chunk UU PDP. **Fix:** rerank gabungan dengan cosine similarity embedding (deployment yang sama dengan indexing), lalu potong ke `top_k` (`_rerank`, `lightrag_backend.py`).
6. **Chunk LightRAG ±4.000 karakter terpotong ke 800 karakter** saat diteruskan ke LLM, sehingga definisi yang dicari ada di karakter ke-616/2.853 dan ikut hilang. **Fix:** batas per sumber 2.500 karakter dan **budget total 16.000 karakter yang sama untuk kedua backend** (`tools/formatting.py`).

> Poin 5–6 ketahuan karena **jawaban eval dibaca manual**: skor 1 dengan 8 sumber itu janggal. Pelajarannya, sebelum menyimpulkan "backend X lebih buruk", periksa dulu adapter dan format konteks milikmu sendiri.

Semuanya dikunci oleh test: [`tests/unit/test_lightrag_up.py`](../tests/unit/test_lightrag_up.py), [`tests/integration/test_lightrag_backend.py`](../tests/integration/test_lightrag_backend.py).

## Coba sendiri

1. Buka WebUI :9622 → tab **Knowledge Graph** → cari entitas "LightRAG". Relasi apa saja yang terbentuk dari 6 paper?
2. Tanyakan hal yang sama ke `library_ragflow` dan `library_lightrag` di `adk web`: "hubungan RAPTOR dengan GraphRAG?". Bandingkan sumber yang dikutip.
3. Ganti `mode` di `retrieve` (`lightrag_backend.py`) dari `mix` ke `naive` (vektor saja). Bagaimana perubahan jawabannya?
