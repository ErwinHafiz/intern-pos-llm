# 07 · Evaluasi: adk eval & RAGFlow vs LightRAG

Ada **dua** jenis evaluasi dengan tujuan berbeda:

| | `adk eval` (tests/eval) | `uv run eval` (cli/eval.py) |
|---|---|---|
| Menjawab | "Apakah **agent** berperilaku benar?" | "Backend **mana** yang menjawab lebih baik?" |
| Cara | Rekaman sesi asli → ulangi → bandingkan trajektori tool | 10 pertanyaan yang sama → 2 backend → LLM-judge |
| Metrik | `tool_trajectory_avg_score`, `response_match_score` | Skor 1–5, latensi, jumlah sumber |

## 1. adk eval: perilaku agent

**Membuat kasus uji** (best practice ADK): jalankan percakapan di `adk web`, lalu buka tab **Eval** → *Add current session* ke eval set. Di project ini 4 kasus direkam dengan cara yang sama lewat API `adk web` (`POST /run` lalu `POST /dev/apps/{app}/eval-sets/{id}/add-session`), kemudian disimpan sebagai [`tests/eval/library_ragflow/routing.test.json`](../tests/eval/library_ragflow/routing.test.json):

| Kasus | Trajektori yang diharapkan |
|---|---|
| `/dataset` | `catalog_agent` → `list_datasets` → `finish_task` |
| `/cari sanksi ...` | `transfer_to_agent` → `search` |
| `/bahas uu pdp` | `transfer_to_agent` → `read_document` |
| `/bandingkan UU PDP vs UU ITE : sanksi` | `compare_agent` → `compare_pipeline` → `finish_task` |

[`test_config.json`](../tests/eval/library_ragflow/test_config.json):
- `tool_trajectory_avg_score` threshold 1.0, `IN_ORDER`, `ignore_args: true`. Urutan tool wajib benar, sementara argumen buatan LLM (misalnya query) boleh berbeda.
- `response_match_score` 0.5 (ROUGE-1). Kata-kata jawaban LLM selalu bervariasi, jadi asersi utamanya adalah trajektori.

Jalankan: `uv run pytest -m eval` (butuh RAGFlow + Azure).

**Pelajaran:** rekaman dari task-agent menyimpan *function response* yang tidak bisa dipasangkan evaluator (`Function call not found for function response ids`). Karena trajectory evaluator hanya butuh *function call*, bagian response dibuang dari rekaman.

## 2. uv run eval: RAGFlow vs LightRAG

```powershell
uv run eval                       # 10 pertanyaan × 2 backend
uv run eval --only q1,q6          # sebagian
uv run eval --backend lightrag
```

- Pertanyaan: [`eval/questions.yaml`](../eval/questions.yaml). Ada 4 *fakta*, 3 *compare*, dan 3 *relasional*. Setiap pertanyaan punya `expected_points` yang diambil dari dokumen asli.
- **Adil:** agent, persona, LLM (`gpt-5.1`), dan embedding (`text-embedding-3-small`) sama. Yang berbeda hanya retrieval.
- **Judge:** LLM yang sama dengan prompt tetap (`JUDGE_PROMPT` di `cli/eval.py`), memberi skor 1–5 terhadap `expected_points`. Jawaban "tidak ditemukan" padahal poinnya ada di dokumen diberi skor 1.
- Hasil: `eval/results/<tanggal>.md` (tabel ringkasan per jenis, per pertanyaan, dan jawaban lengkap dalam `<details>`).

### Cara membaca hasil

1. Lihat **ringkasan per jenis** terlebih dahulu. Hipotesis awalnya: RAGFlow unggul di *fakta* (kutipan halaman, tabel utuh), LightRAG unggul di *relasional* (graph). Cek apakah data mendukung hipotesis ini.
2. Untuk skor yang berbeda jauh, buka `<details>` dan lihat **sumber** yang dikutip. Retrieval yang salah biasanya terlihat di sana.
3. Skor LLM-judge adalah indikasi, bukan kebenaran mutlak. Baca sendiri minimal 3 jawaban.

### Pelajaran dari run pertama

- **Skor rendah ≠ backend buruk.** Run pertama LightRAG mendapat skor 1 di q1–q2 padahal ada 8–9 sumber. Ternyata penyebabnya bug adapter kita (potongan 800 karakter + penggabungan tanpa skor, lihat [06](06-backend-lightrag.md)). Setelah diperbaiki, kedua backend dievaluasi ulang dengan kode yang sama.
- **Filter per dokumen terlalu sempit:** compare per dokumen di LightRAG memfilter hasil *setelah* retrieval. Dengan `top_k` 6, dokumen target sering tidak ikut terambil. Setelah retrieval diperlebar 3× saat ada filter dokumen, q5 naik 3→5 dan q6 naik 4→5 (skor total LightRAG 3,60 → 3,90).
- **Error sesaat:** q2 RAGFlow sempat gagal karena server error sesaat. Pertanyaan itu dijalankan ulang dengan `uv run eval --backend ragflow --only q2`. Hasil digabung per (pertanyaan, backend).
- Backend boleh dijalankan **bergantian** (`--backend ragflow`, lalu `--backend lightrag`) supaya hemat RAM. Hasilnya digabung otomatis ke file tanggal yang sama.

### Keterbatasan (PoC)

- 10 pertanyaan dan satu kali run per pertanyaan: tidak ada uji statistik.
- Judge memakai LLM yang sama dengan penjawab (bias kemungkinan ada).
- LightRAG memakai `gpt-4.1-mini` untuk ekstraksi graph (hemat biaya). Model yang lebih kuat bisa memperbaiki graph-nya.

Hasil terbaru: lihat folder [`eval/results/`](../eval/results/).
