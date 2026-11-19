# 04 · Workflow graph: ingest & compare pipeline

**Tujuan:** tahu kapan memakai `Workflow` (graph deterministik) alih-alih LLM agent, dan bisa membuat sequential chain, routing, serta fan-out paralel.

## Kapan Workflow?

| Pertanyaan | Jawaban → pakai |
|---|---|
| Langkahnya selalu sama dan urut? | **Workflow** (murah, cepat, bisa dites tanpa LLM) |
| Perlu memahami bahasa / memilih secara bebas? | **LlmAgent** |
| Satu aksi atomik? | **Function tool** |

Kedua workflow kita **tidak memanggil LLM sama sekali**. LLM hanya ada di agent yang memanggilnya.

## 1. Sequential chain: `ingest_pipeline`

[`workflows/ingest_pipeline.py:101`](../src/smart_library/workflows/ingest_pipeline.py)

```python
Workflow(
    name="ingest_pipeline",
    edges=[("START", load_file, upload, start_parse, wait_parsed, report)],
    input_schema=IngestRequest,          # wajib agar bisa dipasang sebagai tool
)
```

- Satu tuple = rantai berurutan. Output node A menjadi `node_input` node B.
- Node boleh menerima `ctx: Context` untuk `await ctx.load_artifact(...)` (file yang dilampirkan di chat) dan `ctx.state[...]`.
- **Short-circuit:** tiap node mengembalikan dict ber-`status`. Kalau bukan `success`, node berikutnya meneruskannya apa adanya, sehingga error di `load_file` langsung sampai ke agent.
- **Workflow sebagai tool:** `tools=[make_ingest_pipeline(backend)]` (`agents/ingest.py:15`). ADK membungkusnya jadi `NodeTool` dengan parameter dari `input_schema`.

## 2. Routing + fan-out paralel: `compare_pipeline`

[`workflows/compare_pipeline.py:75`](../src/smart_library/workflows/compare_pipeline.py)

```
resolve_targets ─┬─ route "ok"   ──▶ retrieve_target ×N (paralel) ──▶ build_evidence
                 └─ route "stop" ──▶ stop      (target < 2 / ambigu / backend error)
```

```python
edges=[
    ("START", resolve_targets),
    (resolve_targets, {"ok": retrieve_target, "stop": stop}),   # routing
    (retrieve_target, build_evidence),
]
```

- **Routing:** node memilih cabang dengan `ctx.route = "ok"`. Ini sama dengan `Event(route=...)` di `Research/graph_based_agent` milikmu.
- **Fan-out dinamis:** `@node(parallel_worker=True)` menjalankan `retrieve_target` **sekali untuk setiap item** list output `resolve_targets`, secara paralel, lalu mengumpulkan hasilnya menjadi list untuk `build_evidence`. Jumlah target bebas (2, 3, 5…).

### `parallel_worker` vs `JoinNode`

| | `JoinNode` (yang kamu pakai di `graph_based_agent`) | `parallel_worker=True` (dipakai di sini) |
|---|---|---|
| Jumlah cabang | **Statis**, ditulis di `edges` | **Dinamis**, sebanyak item list |
| Cocok untuk | Router ke beberapa jenis handler berbeda | Operasi yang sama untuk N item |
| Hasil | Gabungan output cabang | List hasil, urut sesuai input |

## Menguji workflow tanpa LLM

[`tests/unit/wf_harness.py`](../tests/unit/wf_harness.py) membungkus workflow dalam workflow "harness" yang menyuntikkan request, lalu menjalankannya dengan `InMemoryRunner`. Hasilnya: 12 test workflow selesai dalam beberapa detik, tanpa biaya token.

## Coba sendiri

1. Tambahkan node `check_size` di `ingest_pipeline` antara `load_file` dan `upload` yang menolak file > 10 MB. Tulis test-nya dulu di `test_ingest_pipeline.py`.
2. Ubah `compare_pipeline` agar menerima maksimal 4 target (route `stop` bila lebih).
3. Buka `adk web`, jalankan `/bandingkan UU PDP vs UU ITE`, lalu buka tab Trace dan temukan `retrieve_target` yang berjalan paralel.

## Kesalahan umum

| Gejala | Solusi |
|---|---|
| `NodeTool requires an explicit Pydantic input_schema` | Beri `input_schema=` pada `Workflow` |
| Parallel worker error "expects list" | Node sebelumnya harus mengembalikan list. Pakai routing untuk jalur error |
| Bytes file ikut tersimpan di event | Jangan kirim bytes antar-node. Kirim nama artifact lalu `load_artifact` di node yang butuh |
