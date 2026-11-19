# 01 · Setup: uv, RAGFlow, LightRAG, Azure OpenAI

**Tujuan:** setelah bab ini, empat komponen berikut hidup di laptop kamu. Semuanya asli, tanpa mock.

| Komponen | Alamat | Untuk apa |
|---|---|---|
| RAGFlow (Docker) | UI `http://localhost` · API `http://localhost/api/v1` | Backend RAG #1 + UI bawaan |
| LightRAG Server "Regulasi Digital ID" | `http://localhost:9621/webui` | Backend RAG #2 (dataset 1) + UI graph |
| LightRAG Server "Riset RAG" | `http://localhost:9622/webui` | Backend RAG #2 (dataset 2) |
| ADK Web | `http://localhost:8000` | UI chat untuk agent kita |

```
           ┌──────────── adk web (:8000) ────────────┐
           │ library_ragflow        library_lightrag │
           └──────┬──────────────────────────┬───────┘
                  ▼                          ▼
        RAGFlow API (:80/9380)      LightRAG :9621 / :9622
                  │                          │
                  └────────► Azure OpenAI ◄──┘   (chat gpt-5.1, embedding text-embedding-3-small)
```

## 1. Prasyarat

- **uv** ≥ 0.9 (`uv --version`)
- **Docker Desktop** menyala
- Repo RAGFlow (`C:\Users\erwin\Intern_POS\ragflow`, v1.0.0)
- Azure OpenAI dengan deployment **chat** (`gpt-5.1`) dan **embedding** (`text-embedding-3-small`)

## 2. Install project

```powershell
cd C:\Users\erwin\Intern_POS\smart-library
uv sync --all-groups      # buat .venv + install ADK, ragflow-sdk, LightRAG server, pytest
copy .env.example .env    # lalu isi nilainya
```

> **Kenapa uv?** `uv.lock` mengunci semua versi, jadi siapa pun yang meng-clone repo ini mendapat lingkungan yang persis sama hanya dengan `uv sync`.

### Mengisi `.env`

| Variabel | Contoh | Catatan |
|---|---|---|
| `LLM_MODEL` | `openai/gpt-5.1` | Endpoint Azure `/openai/v1` kompatibel OpenAI, jadi pakai prefix LiteLLM `openai/` + **nama deployment** |
| `LLM_API_BASE` | `https://<resource>.openai.azure.com/openai/v1` | |
| `LLM_API_KEY` | | Key Azure |
| `EMBEDDING_DEPLOYMENT` | `text-embedding-3-small` | Dipakai **dua** backend supaya adil |
| `LIGHTRAG_LLM_DEPLOYMENT` | `gpt-4.1-mini` | Hanya untuk ekstraksi graph LightRAG (hemat biaya) |
| `RAGFLOW_BASE_URL` | `http://localhost` | Lewat nginx :80 |
| `RAGFLOW_API_KEY` | `ragflow-...` | Langkah 3 |
| `RAGFLOW_EMBEDDING_MODEL` | `text-embedding-3-small@azure-model@OpenAI-API-Compatible` | Persis seperti nama di UI RAGFlow |
| `LIGHTRAG_WORKSPACES` | `Regulasi Digital ID=http://localhost:9621,Riset RAG=http://localhost:9622` | 1 dataset = 1 server |

Cek cara cepat apakah nama deployment benar:

```bash
curl -s $LLM_API_BASE/embeddings -H "api-key: $LLM_API_KEY" -H "content-type: application/json" \
  -d '{"model":"text-embedding-3-small","input":"halo"}' | head -c 200
```

## 3. RAGFlow

```powershell
cd C:\Users\erwin\Intern_POS\ragflow\docker
docker compose -f docker-compose.yml up -d
docker ps          # ragflow-cpu, mysql, es01, minio, redis/kvrocks harus "Up"
```

1. Buka `http://localhost` lalu **Sign up / Login**.
2. **Avatar → Model providers → OpenAI-API-Compatible**: tambahkan
   - chat: nama `gpt-5.1`, base URL `https://<resource>.openai.azure.com/openai/v1`, API key Azure
   - embedding: nama `text-embedding-3-small`, base URL dan key yang sama
3. **System Model Settings** → pilih embedding default `text-embedding-3-small`.
4. **Avatar → API → Create new key**. Salin ke `RAGFLOW_API_KEY`.

Verifikasi dari Python (SDK harus cocok dengan server):

```powershell
uv run python -c "from ragflow_sdk import RAGFlow; from smart_library.config import load_settings as L; s=L(); print([d.name for d in RAGFlow(s.ragflow_api_key, s.ragflow_base_url).list_datasets()])"
```

Hasilnya list (boleh kosong). Kalau muncul error versi API, sesuaikan versi `ragflow-sdk` di `pyproject.toml` dengan versi server.

## 4. LightRAG Server

```powershell
uv run lightrag-up
```

Perintah ini menjalankan **satu proses `lightrag-server` per dataset**, sesuai `LIGHTRAG_WORKSPACES`.

> **Kenapa satu server per dataset?** LightRAG Server v1.5 menyimpan data per *workspace*, tetapi workspace dipilih saat server **start**, bukan per request (header `LIGHTRAG-WORKSPACE` hanya dipakai endpoint status). Jadi setiap dataset dapat port dan WebUI sendiri. Implementasinya di [`src/smart_library/cli/lightrag_up.py`](../src/smart_library/cli/lightrag_up.py).

Konfigurasi LLM/embedding untuk LightRAG **diambil otomatis dari `.env` utama** (binding `openai` diarahkan ke endpoint Azure v1), jadi tidak ada file konfigurasi kedua.

Verifikasi:

```powershell
curl http://localhost:9621/health   # "status":"healthy"
curl http://localhost:9622/health
```

Lalu buka `http://localhost:9621/webui`. Log server ada di `data/lightrag/logs/`.

## 5. Cek semuanya

```powershell
uv run pytest                    # unit test (cepat, tanpa layanan)
uv run pytest -m integration     # butuh RAGFlow + LightRAG hidup
```

## 6. Mematikan

```powershell
# LightRAG: Ctrl+C di terminal lightrag-up
cd C:\Users\erwin\Intern_POS\ragflow\docker; docker compose down   # data tetap tersimpan di volume
```

## Kesalahan umum

| Gejala | Penyebab & solusi |
|---|---|
| `UnicodeEncodeError: 'charmap'` saat LightRAG start | Konsol Windows cp1252. `lightrag-up` sudah men-set `PYTHONUTF8=1`. Kalau menjalankan `lightrag-server` manual, set sendiri |
| `DeploymentNotFound` | Nama di `.env` harus **nama deployment** Azure, bukan nama model katalog |
| `RAGFlow tidak bisa dihubungi` | Docker Desktop mati atau container belum `Up`. Jalankan `docker compose up -d` |
| Port 9621 dipakai | Masih ada `lightrag-server` lama. Matikan prosesnya atau ganti port di `LIGHTRAG_WORKSPACES` |
