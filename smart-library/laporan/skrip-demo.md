# Skrip demo live (±2 menit, setelah slide 4)

## Persiapan (sebelum meeting, ±5 menit)

Jalankan **satu stack berat dalam satu waktu**: untuk demo cukup RAGFlow.

```powershell
cd C:\Users\erwin\Intern_POS\ragflow\docker
docker start docker-es01-1; docker compose -f docker-compose.yml start
cd C:\Users\erwin\Intern_POS\smart-library
uv run adk web agents            # buka http://localhost:8000 → pilih library_ragflow
```

Tutup Edge atau aplikasi berat lain. Cek dengan `/dataset`: harus muncul dua dataset.

## Alur demo

| # | Ketik | Tunjukkan |
|---|---|---|
| 1 | `/bantuan` | Daftar shortcut, dijawab librarian sendiri |
| 2 | `/dataset Regulasi Digital ID` | Tabel 7 dokumen + status (catalog_agent, mode task) |
| 3 | `/bahas uu pdp` | Ringkasan + kutipan `[n] … hlm.`. Buka tab **Trace**: librarian → transfer → research_agent → read_document |
| 4 | `apa sanksi administratifnya?` | Pertanyaan lanjutan tetap di UU PDP (tab **State** → `scope`) |
| 5 | `/bandingkan UU PDP vs UU ITE : sanksi` | Tabel perbandingan. Di Trace terlihat `compare_pipeline` dengan `retrieve_target` paralel |
| 6 | (opsional) lampirkan PDF kecil, lalu `/upload Riset RAG` | ingest_pipeline: upload → parse → siap dibahas. File juga muncul di UI RAGFlow |

## Kalau ada pertanyaan "kenapa tidak pakai LightRAG di demo?"

Bisa. Matikan RAGFlow (`docker compose stop`), jalankan `uv run lightrag-up`, lalu pilih `library_lightrag` di dropdown. Agent-nya identik. Tunjukkan WebUI graph di http://localhost:9622/webui.

## Kalau macet

| Gejala | Tindakan |
|---|---|
| "RAGFlow tidak bisa dihubungi" | `docker ps`. Kalau Elasticsearch tidak jalan: `docker start docker-es01-1` |
| Docker error 500 / laptop berat | `wsl --shutdown`, buka Docker Desktop lagi, lalu ulangi persiapan |
| Jawaban lambat (±10–20 s per hop) | Normal untuk gpt-5.1. Sambil menunggu, jelaskan Trace |
