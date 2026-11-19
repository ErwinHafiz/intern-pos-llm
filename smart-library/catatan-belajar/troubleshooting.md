# Troubleshooting

| Gejala | Penyebab | Solusi |
|---|---|---|
| `Variabel .env wajib belum diisi: LLM_MODEL` | `.env` belum dibuat | `copy .env.example .env` lalu isi |
| `DeploymentNotFound` | Nama deployment Azure salah | Pakai **nama deployment**, bukan nama model katalog. Cek dengan curl di [01-setup](01-setup.md) |
| `RAGFlow tidak bisa dihubungi ... docker compose up` | Docker/RAGFlow mati | Nyalakan Docker Desktop → `docker compose -f docker-compose.yml up -d` di `ragflow/docker` |
| `RAGFlow error: extra inputs are not permitted` | SDK dan server beda versi | Lihat [02](02-ragflow-dasar.md) bagian "Hal yang hanya ketahuan saat mencoba" |
| Dokumen RAGFlow lama sekali di RUNNING | DeepDoc (layout + OCR) di CPU | Normal untuk PDF besar. Pantau di UI RAGFlow. Untuk PDF teks biasa, bisa ganti PDF parser ke *Plain Text* di pengaturan dataset |
| `LightRAG Server tidak aktif ... uv run lightrag-up` | Server LightRAG belum jalan | `uv run lightrag-up`, cek `curl localhost:9621/health` |
| LightRAG: `legacy source file not found` | Env `INPUT_DIR` tidak diset (parser 1.5.7 membaca env, bukan argumen CLI) | Jalankan server lewat `uv run lightrag-up` (sudah men-set `INPUT_DIR`) |
| LightRAG: `UnicodeEncodeError: 'charmap'` | Konsol Windows cp1252 | `lightrag-up` sudah men-set `PYTHONUTF8=1` |
| `Dataset baru ... di LightRAG perlu server baru` | 1 dataset = 1 server LightRAG | Tambah entri di `LIGHTRAG_WORKSPACES`, restart `lightrag-up` |
| `/upload` → "File belum dilampirkan" | Tidak ada lampiran | Klik ikon klip di `adk web`, pilih file, ketik `/upload <dataset>` |
| `[Upload Error: ... exceeds ...]` | File > 20 MB (batas plugin ADK) | Upload lewat `uv run seed` atau UI backend |
| Seed: `Gagal mengunduh ... Unduh manual dari ...` | Situs menolak unduhan otomatis | Buka link, unduh, simpan ke `data/downloads/<filename>` persis, ulangi `uv run seed` |
| Git Bash mengubah `/dataset` jadi `C:/Program Files/Git/dataset` | Konversi path MSYS | Pakai PowerShell, atau `MSYS_NO_PATHCONV=1` |
| Jawaban agent tanpa kutipan / mengarang | Persona dilonggarkan, atau retrieval kosong | Cek tab Trace: apa isi `sources`? Perketat aturan di `prompts/research.md` |
| Tabel dari `/dataset` atau `/bandingkan` hilang | Task agent mengirim ringkasan di `finish_task` | Lihat [05](05-orchestrator.md) "Dua pelajaran dari uji asli" |
