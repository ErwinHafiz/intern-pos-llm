# PRD — Smart Library: Chatbot Dokumen Multi-Agent (Google ADK × RAGFlow × LightRAG)

| | |
|---|---|
| Versi | 1.0 (draft untuk review) |
| Tanggal | 2026-11-19 |
| Pemilik | Erwin (intern) |
| Status | Menunggu persetujuan |
| Dokumentasi | Catatan belajar: [`catatan-belajar/`](../catatan-belajar/) · Dokumentasi teknis: [`docs/dokumentasi-teknis.docx`](../../docs/dokumentasi-teknis.docx) |

---

## 1. Latar belakang & masalah

Saya sedang mendalami **Google ADK** (agent, tools, workflow, routing) dan **RAGFlow**. Kedua hal itu sudah saya pelajari secara terpisah, tetapi belum ada **satu produk utuh** yang menunjukkan bagaimana keduanya disusun jadi chatbot dokumen yang benar-benar bisa dipakai. Akibatnya:

- Saya belum bisa membangun ulang chatbot RAG sendiri dari nol dengan struktur yang jelas.
- Saya belum punya data nyata untuk menjawab pertanyaan *"RAGFlow vs RAG lain, mana yang lebih baik dan untuk apa?"*
- Saya belum punya bahan presentasi progres eksplorasi (ADK & RAGFlow) untuk meeting.

## 2. Tujuan

| # | Tujuan | Ukuran keberhasilan |
|---|---|---|
| G1 | **Produk jadi**: chatbot dokumen multi-agent yang berjalan end-to-end | Demo di `adk web` dengan RAGFlow & LightRAG **asli**: upload, cari, bahas, bandingkan |
| G2 | **Menguasai & bisa membangun ulang** | Tutorial `catatan-belajar/01–08` cukup untuk membangun ulang project tanpa bantuan; tiap konsep ADK punya contoh nyata di kode |
| G3 | **Perbandingan RAGFlow vs LightRAG** yang adil | LLM, embedding, prompt, dan pertanyaan sama; hasil `uv run eval` tersimpan sebagai tabel |
| G4 | **Starter kit** untuk produk berikutnya | Ganti domain cukup lewat `data/sources.yaml` + `prompts/`; tambah backend cukup 1 file di `backends/` |
| G5 | **Bahan meeting progres** | 1 laporan (.docx) + 1 PPT (±6 slide, 3 menit) yang memetakan target eksplorasi RAGFlow & ADK |

## 3. Non-goals (sengaja TIDAK dikerjakan)

- UI kustom (React/Streamlit). Antarmuka cukup `adk web` + UI bawaan RAGFlow & LightRAG.
- Deployment produksi, autentikasi multi-user, Cloud Run/Agent Engine (hanya dijelaskan jalurnya di docs).
- Evaluasi riset yang berat (RAGAS, puluhan metrik, uji statistik). Evaluasinya ringan karena ini PoC.
- Data dummy atau teks karangan AI sebagai isi koleksi.
- Dokumen internal tempat magang.

## 4. Pengguna & skenario

**Pengguna utama:** pembelajar/pengembang (saya), lalu rekan tim yang menonton demo.
**Pengguna akhir yang disimulasikan:** pustakawan/analis yang punya kumpulan dokumen dan ingin cepat memahami, mencari, dan membandingkan isinya.

| Skenario | Contoh percakapan |
|---|---|
| S1 Lihat koleksi | `/dataset`, "dokumen apa saja di Riset RAG?" |
| S2 Upload & simpan | (lampirkan PDF) "simpan ke Regulasi Digital ID lalu ringkas" |
| S3 Cari | `/cari sanksi administratif kebocoran data` |
| S4 Bahas dokumen | `/bahas UU 27 2022`, lalu tanya lanjutan multi-turn |
| S5 Bandingkan file vs file | `/bandingkan UU PDP vs UU ITE : kewajiban penyelenggara` |
| S6 Bandingkan dataset vs dataset | `/bandingkan Regulasi Digital ID vs Riset RAG : bagaimana privasi dibahas?` |
| S7 Bandingkan file vs dataset | `/bandingkan paper LightRAG vs dataset Regulasi Digital ID` |
| S8 Bandingkan backend | Pertanyaan sama ke agent `library_ragflow` dan `library_lightrag` (dropdown `adk web`) + `uv run eval` |

## 5. Kebutuhan fungsional

| ID | Kebutuhan | Prioritas |
|---|---|---|
| F1 | Menampilkan daftar dataset & dokumen beserta status parsing | Wajib |
| F2 | Memilih *scope* aktif (dataset/dokumen) yang dipakai untuk pertanyaan berikutnya | Wajib |
| F3 | Upload file apa pun yang didukung backend (PDF, DOCX, XLSX, PPTX, TXT/MD) lewat lampiran chat, disimpan ke dataset pilihan, di-parse, dan diberi status | Wajib |
| F4 | Pencarian semantik dengan kutipan sumber (nama dokumen + lokasi) | Wajib |
| F5 | Bahas/ringkas satu dokumen + tanya jawab lanjutan multi-turn | Wajib |
| F6 | Bandingkan ≥2 **target**, dengan target berupa dataset atau file dalam kombinasi apa pun, opsional disertai pertanyaan fokus. Output berupa tabel persamaan/perbedaan dengan kutipan | Wajib |
| F7 | Shortcut chat: `/dataset`, `/cari`, `/bahas`, `/bandingkan`, `/upload`, `/bantuan` | Wajib |
| F8 | Dua agent identik yang hanya beda backend: `library_ragflow` & `library_lightrag` | Wajib |
| F9 | `uv run seed`: unduh dokumen publik asli → buat dataset → upload → parse, di kedua backend | Wajib |
| F10 | `uv run eval`: ±10 pertanyaan ke kedua backend → tabel Markdown (jawaban, sumber, latensi) | Wajib |
| F11 | Tidak mengarang: jika sumber tidak memuat jawaban, agent mengatakannya | Wajib |
| F12 | Error yang jelas dan bisa ditindaklanjuti (mis. "RAGFlow mati — jalankan docker compose up") | Wajib |

## 6. Kebutuhan non-fungsional

- **Nyata, bukan dummy.** Produk, seed, eval, integration test, dan demo memakai RAGFlow (Docker), LightRAG Server, serta Azure OpenAI sungguhan. *FakeBackend hanya boleh di `tests/unit`.*
- **UI bawaan tetap jalan.** Dokumen hasil seed/upload terlihat di **RAGFlow Web UI** (`http://localhost`) dan **LightRAG WebUI** (`http://localhost:9621`, termasuk graph).
- **Mengikuti best practice ADK.** Paket agent dengan `__init__.py` + `agent.py` yang mengekspor `app = App(...)`; sub-agent `mode`; graph Workflow untuk proses deterministik; `adk eval` untuk evaluasi perilaku agent.
- **uv** untuk semua hal (`uv sync`, `uv run ...`). Python 3.12.
- **Mudah dibaca.** 1 file = 1 tanggung jawab; persona di `prompts/*.md`; dependency satu arah.
- **Rahasia aman.** `.env` tidak di-commit; ada `.env.example`.
- **Bahasa.** Agent menjawab dalam bahasa pengguna (default Indonesia). Docs dan laporan berbahasa Indonesia.

## 7. Koleksi awal (dokumen publik asli, beragam format)

| Dataset | Isi (rencana, URL diverifikasi saat implementasi) | Format |
|---|---|---|
| **Regulasi Digital ID** | UU 27/2022 PDP, UU 1/2024 (perubahan kedua UU ITE), Perpres 95/2018 SPBE, Strategi Nasional Kecerdasan Artifisial 2020–2045, SE Menkominfo 9/2023 tentang Etika AI, tabel statistik BPS terkait TIK | PDF, XLSX, DOCX bila tersedia dari sumber resmi |
| **Riset RAG** | Lewis et al. 2020 (RAG), LightRAG 2024, GraphRAG 2024, RAPTOR 2024, Self-RAG 2023, survei RAG Gao et al. 2023 | PDF (arXiv), plus PPTX/DOCX publik bila tersedia |

File **tidak di-commit**. Repo hanya menyimpan `data/sources.yaml` (URL + lisensi + dataset tujuan).

## 8. Kriteria penerimaan (Definition of Done)

1. `uv sync` lalu `uv run seed` sukses; kedua dataset terlihat di RAGFlow UI dan LightRAG WebUI.
2. `uv run adk web agents` menampilkan `library_ragflow` dan `library_lightrag`; skenario S1–S7 berhasil di **keduanya** (atau mengembalikan `unsupported` yang jelas untuk keterbatasan LightRAG yang terdokumentasi).
3. Trace `adk web` memperlihatkan orchestrator → sub-agent → workflow node.
4. `uv run pytest tests/unit` hijau; `tests/integration` dan `adk eval` (tests/eval) hijau dengan backend hidup.
5. `uv run eval` menghasilkan `eval/results/<tanggal>.md`.
6. README + `catatan-belajar/01–08` + troubleshooting lengkap.
7. `laporan/` berisi laporan .docx + PPT 3 menit.

## 9. Milestone

| M | Isi | Output |
|---|---|---|
| M0 | Setup: uv project, `.env`, RAGFlow Docker up, LightRAG Server up, verifikasi API | `catatan-belajar/01-setup.md` |
| M1 | Backend RAGFlow + tools katalog/search + orchestrator & sub-agent | Demo S1, S3, S4 |
| M2 | Workflow ingest (upload) + compare | Demo S2, S5–S7 |
| M3 | Seed dokumen asli + adk eval + integration test | DoD 1, 3, 4 |
| M4 | Backend LightRAG + agent kedua + `uv run eval` | DoD 2, 5 |
| M5 | Docs tutorial + README + laporan & PPT | DoD 6, 7 |
| M6 *(nanti, di luar scope saat ini)* | Deploy agent ADK ke **Google Cloud Vertex AI (Agent Engine / Cloud Run)** | Rencana & spec terpisah |

## 10. Risiko

| Risiko | Mitigasi |
|---|---|
| Biaya token ekstraksi graph LightRAG | Koleksi dijaga ±12 dokumen; model ekstraksi bisa diatur terpisah (`LIGHTRAG_LLM_DEPLOYMENT`) |
| Parsing RAGFlow lambat di laptop | Polling dengan timeout 5 menit + pesan "masih diproses"; seed dijalankan sekali |
| LightRAG Server v1.4.15 tidak mendukung workspace per request (terverifikasi) | 1 server per dataset (port 9621, 9622) via `uv run lightrag-up` |
| API ADK 2.x masih berubah | Versi di-pin di `uv.lock`; pola dicek ke kode terpasang & adk.dev |
| Sumber resmi tidak menyediakan DOCX/PPTX | Hanya pakai file yang benar-benar dipublikasikan; laporkan bila format tertentu tidak ada, jangan dibuat-buat |
