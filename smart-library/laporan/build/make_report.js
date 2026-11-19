// Generator laporan progres: node laporan/build/make_report.js
// Butuh: npm i docx@9.5.1 (NODE_PATH ke node_modules-nya). Angka dibaca dari eval/results/<tanggal>.json.
const path = require("path");
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell, WidthType, ShadingType,
  AlignmentType, ImageRun, LevelFormat, BorderStyle, Footer, PageNumber,
} = require("docx");

const ROOT = path.resolve(__dirname, "..", "..");
const IMG = path.join(ROOT, "catatan-belajar", "img");
const DATE = process.argv[2] || "2026-11-19";
const rows = JSON.parse(fs.readFileSync(path.join(ROOT, "eval", "results", `${DATE}.json`), "utf8"));
const FINDINGS = JSON.parse(fs.readFileSync(path.join(__dirname, "findings.json"), "utf8"));

const mean = (xs) => (xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : 0);
const score = (b, t) => mean(rows.filter((r) => r.backend === b && (!t || r.type === t)).map((r) => r.score));
const lat = (b) => mean(rows.filter((r) => r.backend === b).map((r) => r.latency_s));
const med = (b) => { const v = rows.filter((r) => r.backend === b).map((r) => r.latency_s).sort((x, y) => x - y); const m = v.length >> 1; return v.length % 2 ? v[m] : (v[m - 1] + v[m]) / 2; };
const n = (x, d = 2) => x.toFixed(d).replace(".", ",");
const TEAL = "0F3D3E", ICE = "E6F0EF", FONT = "Calibri";
const CONTENT_W = 9026; // A4 dengan margin 1"

const p = (text, opts = {}) => new Paragraph({ spacing: { after: 120 }, ...opts, children: [].concat(text).map((t) => (typeof t === "string" ? new TextRun(t) : t)) });
const b = (t) => new TextRun({ text: t, bold: true });
const h1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)] });
const h2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)] });
const bullet = (children) => new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 60 }, children: [].concat(children).map((t) => (typeof t === "string" ? new TextRun(t) : t)) });

function table(header, body, widths) {
  const cell = (t, i, head) => new TableCell({
    width: { size: widths[i], type: WidthType.DXA },
    shading: head ? { type: ShadingType.CLEAR, color: "auto", fill: TEAL } : undefined,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    children: [new Paragraph({ children: [new TextRun({ text: String(t), bold: head, color: head ? "FFFFFF" : undefined, size: 20 })] })],
  });
  return new Table({
    width: { size: widths.reduce((a, c) => a + c, 0), type: WidthType.DXA },
    columnWidths: widths,
    rows: [new TableRow({ tableHeader: true, children: header.map((t, i) => cell(t, i, true)) }), ...body.map((r) => new TableRow({ children: r.map((t, i) => cell(t, i, false)) }))],
  });
}

function image(file, wPx, hPx, caption) {
  const w = 600, h = Math.round((hPx / wPx) * w);
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120 }, children: [new ImageRun({ type: "png", data: fs.readFileSync(path.join(IMG, file)), transformation: { width: w, height: h }, altText: { title: caption, description: caption, name: file } })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 }, children: [new TextRun({ text: caption, italics: true, size: 18, color: "5B6770" })] }),
  ];
}

const TYPES = [["fakta", "Fakta (1 dokumen)"], ["compare", "Bandingkan"], ["relasional", "Relasional / lintas dokumen"]];
const winner = (a, c) => (Math.abs(a - c) < 0.05 ? "seri" : a > c ? "RAGFlow" : "LightRAG");
const ids = [...new Set(rows.map((r) => r.id))];
const get = (id, bk) => rows.find((r) => r.id === id && r.backend === bk) || {};

const children = [
  new Paragraph({ heading: HeadingLevel.TITLE, children: [new TextRun("Laporan Progres Eksplorasi RAGFlow & Google ADK")] }),
  p([new TextRun({ text: "Smart Library: chatbot dokumen multi-agent dengan perbandingan RAGFlow vs LightRAG", italics: true })]),
  p([b("Penyusun: "), "Erwin   ", b("Tanggal: "), "19 November 2026   ", b("Repo: "), "smart-library (branch feat/smart-library)"]),

  h1("Ringkasan"),
  p(`Eksplorasi dilakukan dengan membangun produk nyata, bukan contoh terpisah. Smart Library adalah chatbot berbasis Google ADK yang bisa mengupload, mencari, membahas, dan membandingkan dokumen maupun dataset. Chatbot ini memakai RAGFlow atau LightRAG sebagai backend retrieval yang bisa ditukar. Pada 10 pertanyaan uji dengan agent, LLM (gpt-5.1), dan embedding yang sama, skor rata-rata RAGFlow ${n(score("ragflow"), 2)} dan LightRAG ${n(score("lightrag"), 2)} dari 5.`),
  table(["Target eksplorasi", "Status", "Bukti"], [
    ["RAGFlow: paham tools, alur, fungsi", "Selesai", "Bagian 1; adapter backends/ragflow_backend.py; catatan-belajar/02"],
    ["RAGFlow: perbandingan dengan RAG lain", "Selesai", "Bagian 2; eval/results/2026-11-19.md"],
    ["RAGFlow: presentasi 3 menit (PPT)", "Selesai", "laporan/Presentasi-RAGFlow-vs-LightRAG.pptx"],
    ["ADK: paham tools", "Selesai", "Bagian 3; tools/*.py; catatan-belajar/03"],
    ["ADK: paham workflow", "Selesai", "Bagian 3; workflows/*.py; catatan-belajar/04–05"],
    ["ADK: dokumentasi teknis", "Selesai", "README + docs/dokumentasi-teknis.docx + catatan-belajar/"],
    ["ADK: present", "Selesai", "Slide 3–4 + demo adk web"],
  ], [3200, 1300, 4526]),

  h1("1. RAGFlow: tools, alur, dan fungsi"),
  p("Alur RAGFlow: upload ke dataset → parsing DeepDoc (layout, tabel, OCR) → chunking → embedding → index Elasticsearch → hybrid search (vektor + kata kunci) → chunk beserta skor dan nomor halaman."),
  table(["Fungsi (SDK/REST)", "Kegunaan di Smart Library"], [
    ["list_datasets / dataset", "Katalog koleksi (/dataset)"],
    ["upload_documents", "Upload dari chat (/upload) dan seed"],
    ["async_parse_documents / cancel", "Parsing di background + pemantauan status"],
    ["retrieve(dataset_ids, document_ids)", "Pencarian, bahas dokumen, dan bandingkan per target"],
  ], [3600, 5426]),
  ...image("ragflow-dataset-regulasi.png", 1536, 674, "Gambar 1. Dataset Regulasi Digital ID di RAGFlow: 7 dokumen asli beserta jumlah chunk."),
  ...image("ragflow-chunks-uupdp.png", 1536, 674, "Gambar 2. Hasil chunk DeepDoc untuk UU 27/2022 (66 chunk)."),
  h2("Temuan teknis RAGFlow v1.0 + SDK 0.26"),
  bullet("create_dataset dari SDK mengirim field yang ditolak server v1.0. Solusinya POST /datasets langsung (name, parser_id, parse_type, embedding_model)."),
  bullet("Status run kadang tetap \"0\" walau parsing selesai, sehingga status dihitung dari run + progress."),
  bullet("Filter name= untuk dokumen yang belum ada menghasilkan error; page_size dibatasi maksimal 100."),
  bullet("Parsing DeepDoc di CPU berat. Saat RAM laptop habis, Docker error 500 dan DNS internal rusak sehingga parsing tertahan. Solusinya restart stack. Dua dokumen besar (Stranas KA 180 halaman, Perpres 95/2018) di-parse dengan mode Plain Text."),

  h1("2. Perbandingan RAGFlow vs LightRAG"),
  p("Desain uji yang adil: kedua backend hanya dipakai untuk retrieval, dan jawaban selalu ditulis agent ADK yang sama. Koleksi terdiri dari 13 dokumen publik asli dalam 2 dataset (regulasi digital Indonesia dan paper riset RAG). Ada 10 pertanyaan: 4 fakta, 3 bandingkan, dan 3 relasional. Setiap jawaban dinilai 1–5 oleh LLM-judge terhadap poin kunci dari dokumen."),
  table(["Jenis pertanyaan", "RAGFlow", "LightRAG", "Unggul"],
    [...TYPES.map(([t, l]) => [l, n(score("ragflow", t), 2), n(score("lightrag", t), 2), winner(score("ragflow", t), score("lightrag", t))]),
     ["Total", n(score("ragflow"), 2), n(score("lightrag"), 2), winner(score("ragflow"), score("lightrag"))],
     ["Median latensi (detik)", n(med("ragflow"), 1), n(med("lightrag"), 1), med("ragflow") < med("lightrag") ? "RAGFlow" : "LightRAG"],
     ["Rata-rata latensi (detik)", n(lat("ragflow"), 1), n(lat("lightrag"), 1), "LightRAG: 1 outlier 648 s"]],
    [3626, 1800, 1800, 1800]),
  p(""),
  table(["ID", "Jenis", "RAGFlow", "LightRAG", "Catatan"], ids.map((id) => [id, get(id, "ragflow").type, get(id, "ragflow").score ?? "-", get(id, "lightrag").score ?? "-", FINDINGS.per_question[id] || ""]), [600, 1200, 1000, 1000, 5226]),
  h2("Temuan utama"),
  ...FINDINGS.key.map((t) => bullet(t)),
  ...image("lightrag-graph-riset.png", 1536, 730, "Gambar 3. Knowledge graph LightRAG dari 6 paper riset RAG (tampilan dibatasi 1000 node)."),
  h2("Perbedaan karakter"),
  table(["Aspek", "RAGFlow", "LightRAG"], [
    ["Parsing", "DeepDoc: layout, tabel, OCR, nomor halaman", "Ekstraksi teks biasa, cepat"],
    ["Biaya indexing", "Tanpa LLM (hanya embedding)", "LLM per chunk untuk ekstraksi graph (gpt-4.1-mini)"],
    ["Konteks retrieval", "Chunk + skor + halaman", "Chunk + entitas + relasi graph, tanpa skor/halaman"],
    ["Multi-dataset", "Native", "1 server per dataset (workspace ditetapkan saat start)"],
    ["Kebutuhan sumber daya", "Docker + Elasticsearch (RAM besar)", "Proses Python ringan"],
  ], [2200, 3413, 3413]),
  h2("Keterbatasan uji"),
  bullet("PoC: 10 pertanyaan, 1 run per pertanyaan, tanpa uji statistik. Hasilnya indikatif."),
  bullet("Judge memakai LLM yang sama dengan penjawab, sehingga bias mungkin ada. Beberapa jawaban sudah dibaca manual."),
  bullet("Angka final: run ulang penuh kedua backend setelah perbaikan adapter (budget konteks sama, rerank LightRAG), ditambah q5–q6 LightRAG yang dijalankan ulang setelah perbaikan filter per dokumen. Tidak ada error pada run final."),
  bullet("Stranas KA dan Perpres 95/2018 di RAGFlow memakai parser Plain Text, bukan DeepDoc."),

  h1("3. Google ADK: tools, workflow, orchestrator"),
  ...image("adk-web-bahas-trace.png", 1440, 900, "Gambar 4. Trace adk web untuk /bahas: librarian → transfer → research_agent → read_document."),
  table(["Konsep ADK", "Dipakai untuk", "Lokasi kode"], [
    ["LlmAgent + function tool + ToolContext/state", "Aksi atomik: list, search, read_document, set_scope", "tools/catalog_tools.py, research_tools.py"],
    ["Orchestrator + sub-agent (mode chat/task/single_turn)", "librarian mendelegasikan ke 4 spesialis", "agents/*.py, prompts/*.md"],
    ["Workflow graph (sequential)", "ingest_pipeline: load → upload → parse → wait → report", "workflows/ingest_pipeline.py"],
    ["Workflow routing + parallel_worker", "compare_pipeline: fan-out ke N target secara paralel", "workflows/compare_pipeline.py"],
    ["App + SaveFilesAsArtifactsPlugin", "Lampiran chat menjadi artifact yang bisa di-upload", "app.py"],
    ["adk eval (AgentEvaluator)", "Mengunci routing shortcut: 4/4 kasus lulus", "tests/eval/"],
  ], [3000, 3326, 2700]),
  p("Aturan memilih: keputusan berbasis bahasa memakai LLM agent; langkah tetap memakai Workflow (murah, cepat, bisa dites tanpa LLM); aksi atomik memakai function tool.", { spacing: { before: 200, after: 120 } }),

  h1("4. Dokumentasi teknis"),
  bullet("PRD: prd/PRD.md. Dokumentasi teknis (riset tools): docs/dokumentasi-teknis.docx di root repo."),
  bullet("Catatan belajar / tutorial bangun ulang: catatan-belajar/01-setup sampai 08-bikin-produk-sendiri, plus troubleshooting."),
  bullet("Kualitas: 89 unit test (FakeBackend hanya di unit test), integration test ke RAGFlow & LightRAG asli, adk eval, dan eval perbandingan."),
  bullet("Dikelola dengan uv (uv sync, uv run seed / eval / lightrag-up / adk web agents)."),

  h1("5. Langkah berikutnya"),
  ...FINDINGS.next.map((t) => bullet(t)),
];

const doc = new Document({
  creator: "Erwin", title: "Laporan Progres Eksplorasi RAGFlow & Google ADK",
  styles: {
    default: { document: { run: { font: FONT, size: 22 } } },
    paragraphStyles: [
      { id: "Title", name: "Title", basedOn: "Normal", run: { font: "Cambria", size: 44, bold: true, color: TEAL }, paragraph: { spacing: { before: 0, after: 120 }, keepNext: true } },
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: "Cambria", size: 32, bold: true, color: TEAL }, paragraph: { spacing: { before: 360, after: 120 }, keepNext: true, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: "Cambria", size: 26, bold: true, color: "3E7C7B" }, paragraph: { spacing: { before: 240, after: 100 }, keepNext: true, outlineLevel: 1 } },
    ],
  },
  numbering: { config: [{ reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] }] },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [new TextRun({ children: ["Halaman ", PageNumber.CURRENT], size: 18, color: "5B6770" })] })] }) },
    children,
  }],
});

const out = path.join(ROOT, "laporan", "Laporan-Progres-Eksplorasi-ADK-RAGFlow.docx");
Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(out, buf); console.log("wrote", out); });
