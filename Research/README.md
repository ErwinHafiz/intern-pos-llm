# Research: agent latihan Google ADK

Folder ini berisi agent yang saya buat sambil mempelajari ADK, dari yang paling sederhana sampai workflow dengan router. Masing-masing berdiri sendiri dan bisa dijalankan lewat `adk web`.

| Agent | Yang dipelajari |
| --- | --- |
| `my_agent/` | Single agent dengan satu function tool (`get_current_time`), model Azure OpenAI lewat `LiteLlm` |
| `second_agent/` | Dua tools (`get_weather`, `get_current_time`) dengan docstring lengkap, dan pengaruh docstring terhadap pemilihan tool oleh LLM |
| `graph_based_agent/` | ADK 2.x `Workflow`: classifier LLM → fungsi router → cabang (BUG / CUSTOMER_SUPPORT / LOGISTICS / RAGFLOW) → `JoinNode` → aggregator. Cabang RAGFLOW memanggil `ragflow_sdk` untuk melihat dataset |

Di file `graph_based_agent/agent.py` juga ada versi workflow sequential dan routing tanpa join yang di-comment, sebagai pembanding.

## Menjalankan

```powershell
cd Research
python -m venv .venv; .venv\Scripts\activate
pip install google-adk litellm python-dotenv ragflow-sdk
copy .env.example my_agent\.env      # ulangi untuk agent lain, lalu isi nilainya
adk web                              # buka http://localhost:8000, pilih agent di dropdown
```

`adk web` dijalankan dari folder `Research`, bukan dari dalam folder agent. Setiap agent membaca `.env` di foldernya sendiri.

Agent-agent ini dibuat dengan Azure OpenAI. Untuk provider lain yang kompatibel OpenAI, cukup ganti `model`, `api_base`, dan `api_key` di `LiteLlm(...)`.
