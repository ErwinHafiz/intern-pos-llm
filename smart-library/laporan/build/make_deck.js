// Generator PPT 3 menit: node laporan/build/make_deck.js
// Butuh: npm i pptxgenjs@3.12.0 react-icons react react-dom sharp (NODE_PATH ke node_modules-nya)
// Angka dibaca dari eval/results/<tanggal>.json, bukan diketik manual.
const path = require("path");
const fs = require("fs");
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const { FaBookOpen, FaProjectDiagram, FaSitemap, FaSearch, FaBalanceScale, FaCloudUploadAlt, FaLightbulb, FaRocket, FaFilePdf, FaLayerGroup } = require("react-icons/fa");

const ROOT = path.resolve(__dirname, "..", "..");
const IMG = path.join(ROOT, "catatan-belajar", "img");
const DATE = process.argv[2] || "2026-11-19";
const rows = JSON.parse(fs.readFileSync(path.join(ROOT, "eval", "results", `${DATE}.json`), "utf8"));

const THEME = {
  name: "Smart Library",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "14292B", lt1: "FFFFFF", dk2: "0F3D3E", lt2: "E6F0EF",
    accent1: "0F3D3E", accent2: "F2A541", accent3: "3E7C7B", accent4: "C8553D",
    accent5: "8AB0AB", accent6: "5B6770", hlink: "3E7C7B", folHlink: "5B6770",
  },
};
const HEX = { teal: "0F3D3E", amber: "F2A541", mid: "3E7C7B", ice: "E6F0EF", rust: "C8553D", gray: "5B6770", ink: "14292B" };

// ---------- data ----------
const mean = (xs) => (xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : 0);
const score = (b, t) => mean(rows.filter((r) => r.backend === b && (!t || r.type === t)).map((r) => r.score));
const lat = (b) => mean(rows.filter((r) => r.backend === b).map((r) => r.latency_s));
const med = (b) => { const v = rows.filter((r) => r.backend === b).map((r) => r.latency_s).sort((x, y) => x - y); const m = v.length >> 1; return v.length % 2 ? v[m] : (v[m - 1] + v[m]) / 2; };
const TYPES = ["fakta", "compare", "relasional"];
const TYPE_LABEL = { fakta: "Fakta", compare: "Bandingkan", relasional: "Relasional" };

async function icon(Comp, color, size = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Comp, { color: "#" + color, size: String(size) }));
  const png = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + png.toString("base64");
}

(async () => {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5
  pres.title = "Eksplorasi RAGFlow dan Google ADK";
  pres.author = "Erwin";
  pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
  const C = pres.SchemeColor;

  pres.defineSlideMaster({
    title: "DARK", background: { color: HEX.teal },
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.3, w: 11.7, h: 1.4, fontSize: 44, bold: true, color: C.background1, fontFace: THEME.headFontFace, valign: "bottom", align: "left", margin: 0 }, text: "" } },
      { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 3.85, w: 11.7, h: 1.2, fontSize: 20, color: C.background2, align: "left", margin: 0 }, text: "" } },
    ],
  });
  pres.defineSlideMaster({
    title: "CONTENT", background: { color: "FFFFFF" },
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.35, w: 12.1, h: 0.9, fontSize: 32, bold: true, color: C.text2, fontFace: THEME.headFontFace, valign: "middle", align: "left", margin: 0 }, text: "" } },
    ],
    slideNumber: { x: 12.4, y: 7.0, w: 0.6, h: 0.3, fontSize: 10, color: HEX.gray },
  });

  const ic = {
    book: await icon(FaBookOpen, "FFFFFF"), graph: await icon(FaProjectDiagram, "FFFFFF"), tree: await icon(FaSitemap, "FFFFFF"),
    search: await icon(FaSearch, "FFFFFF"), scale: await icon(FaBalanceScale, "FFFFFF"), upload: await icon(FaCloudUploadAlt, "FFFFFF"),
    bulb: await icon(FaLightbulb, "FFFFFF"), rocket: await icon(FaRocket, "FFFFFF"), pdf: await icon(FaFilePdf, "FFFFFF"), layers: await icon(FaLayerGroup, "FFFFFF"),
  };
  const circleIcon = (slide, data, x, y, d, fill, name) => {
    slide.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill }, line: { color: fill }, objectName: name + "-circle" });
    const p = d * 0.26;
    slide.addImage({ data, x: x + p, y: y + p, w: d - 2 * p, h: d - 2 * p, objectName: name + "-icon" });
  };

  // ---------- 1. Judul ----------
  pres.addSection({ title: "Pembuka" });
  let s = pres.addSlide({ masterName: "DARK", sectionTitle: "Pembuka" });
  s.addText("Eksplorasi RAGFlow & Google ADK", { placeholder: "title" });
  s.addText("Smart Library: chatbot dokumen multi-agent + perbandingan RAGFlow vs LightRAG", { placeholder: "body" });
  circleIcon(s, ic.book, 0.8, 1.0, 1.0, HEX.amber, "title");
  s.addText("Erwin · Progress eksplorasi · 19 November 2026", { x: 0.8, y: 6.4, w: 8, h: 0.4, fontSize: 14, color: HEX.amber, isTextBox: true, margin: 0 });
  s.addNotes("Selamat siang. Dalam 3 menit saya tunjukkan hasil eksplorasi RAGFlow dan Google ADK dalam bentuk produk nyata: Smart Library, chatbot dokumen multi-agent. Di akhir ada perbandingan RAGFlow dengan LightRAG pada pertanyaan dan dokumen yang sama.");

  // ---------- 2. RAGFlow ----------
  pres.addSection({ title: "RAGFlow" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "RAGFlow" });
  s.addText("RAGFlow: dari dokumen mentah ke kutipan", { placeholder: "title" });
  const steps = [["Upload", "PDF, DOCX, CSV ke dataset", ic.upload], ["DeepDoc", "Layout, tabel, OCR", ic.pdf], ["Chunk + embed", "text-embedding-3-small", ic.layers], ["Hybrid search", "Vektor + kata kunci → chunk + halaman", ic.search]];
  steps.forEach(([t, d, im], i) => {
    const x = 0.6 + i * 1.95;
    circleIcon(s, im, x + 0.45, 1.55, 0.9, i === 1 ? HEX.amber : HEX.mid, "flow" + i);
    s.addText(t, { x, y: 2.55, w: 1.8, h: 0.4, fontSize: 16, bold: true, color: HEX.teal, align: "center", isTextBox: true, margin: 0 });
    s.addText(d, { x, y: 2.95, w: 1.8, h: 0.75, fontSize: 12, color: HEX.gray, align: "center", isTextBox: true, margin: 0 });
    if (i < 3) s.addText("→", { x: x + 1.65, y: 1.75, w: 0.4, h: 0.5, fontSize: 24, color: HEX.amber, align: "center", isTextBox: true, margin: 0 });
  });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 4.1, w: 7.6, h: 2.1, fill: { color: HEX.ice }, line: { color: HEX.ice }, rectRadius: 0.12, objectName: "ragflow-facts" });
  s.addText([
    { text: "Yang dipakai lewat SDK/REST", options: { bold: true, color: HEX.teal, breakLine: true } },
    { text: "dataset · upload_documents · async_parse_documents · retrieve(dataset_ids, document_ids)", options: { breakLine: true } },
    { text: " ", options: { breakLine: true } },
    { text: "Temuan v1.0 + SDK 0.26", options: { bold: true, color: HEX.teal, breakLine: true } },
    { text: "create_dataset ditolak server, status run kadang tetap \"0\", page_size ≤ 100. Semua ditangani di adapter.", options: {} },
  ], { x: 0.85, y: 4.25, w: 7.1, h: 1.8, fontSize: 14, color: HEX.ink, valign: "top", isTextBox: true, margin: 0 });
  s.addImage({ path: path.join(IMG, "ragflow-chunks-uupdp.png"), x: 8.5, y: 1.5, w: 4.3, h: 1.89, objectName: "ragflow-chunks" });
  s.addImage({ path: path.join(IMG, "ragflow-dataset-regulasi.png"), x: 8.5, y: 3.6, w: 4.3, h: 1.89, objectName: "ragflow-files" });
  s.addText("Atas: chunk UU PDP hasil DeepDoc. Bawah: 7 dokumen + jumlah chunk", { x: 8.5, y: 5.6, w: 4.3, h: 0.5, fontSize: 11, color: HEX.gray, italic: true, isTextBox: true, margin: 0 });
  s.addNotes("RAGFlow mengubah dokumen mentah menjadi potongan yang bisa dikutip. Kekuatan utamanya DeepDoc, yang membaca layout, tabel, dan nomor halaman. Saya memakainya lewat SDK: buat dataset, upload, parse, lalu retrieve. Saya juga menemukan beberapa ketidakcocokan antara SDK 0.26 dan server versi 1.0, dan semuanya sudah ditangani serta didokumentasikan.");

  // ---------- 3. ADK ----------
  pres.addSection({ title: "Google ADK" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Google ADK" });
  s.addText("ADK: satu orchestrator, empat spesialis, dua workflow", { placeholder: "title" });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 5.0, y: 1.45, w: 3.3, h: 0.85, fill: { color: HEX.teal }, line: { color: HEX.teal }, rectRadius: 0.12, objectName: "librarian" });
  s.addText([{ text: "librarian", options: { bold: true, breakLine: true } }, { text: "orchestrator · kenali /shortcut", options: { fontSize: 12 } }], { x: 5.0, y: 1.45, w: 3.3, h: 0.85, fontSize: 16, color: "FFFFFF", align: "center", valign: "middle", isTextBox: true, margin: 0 });
  const subs = [["catalog_agent", "mode task", "list · scope"], ["ingest_agent", "mode single_turn", "Workflow ingest"], ["research_agent", "mode chat", "search · read_document"], ["compare_agent", "mode task", "Workflow compare"]];
  subs.forEach(([n, m, t], i) => {
    const x = 0.6 + i * 3.1;
    const cx = x + 1.4, left = Math.min(6.65, cx), w = Math.max(Math.abs(cx - 6.65), 0.01);
    s.addShape(pres.shapes.LINE, { x: left, y: 2.3, w, h: 0.75, line: { color: "8AB0AB", width: 1.5 }, flipH: cx < 6.65, objectName: "edge" + i });
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 3.05, w: 2.8, h: 1.25, fill: { color: HEX.ice }, line: { color: HEX.mid, width: 1 }, rectRadius: 0.1, objectName: "sub" + i });
    s.addText([{ text: n, options: { bold: true, color: HEX.teal, breakLine: true } }, { text: m, options: { color: HEX.rust, fontSize: 12, breakLine: true } }, { text: t, options: { color: HEX.gray, fontSize: 12 } }], { x, y: 3.05, w: 2.8, h: 1.25, fontSize: 15, align: "center", valign: "middle", isTextBox: true, margin: 0 });
  });
  const cards = [["Sub-agent + mode", "chat = transfer, ngobrol bebas · task = kerjakan lalu finish_task · single_turn = dipanggil seperti tool", ic.tree], ["Workflow graph", "ingest: START → load → upload → parse → wait → report. compare: routing + parallel_worker (fan-out N target)", ic.graph], ["Backend bisa ditukar", "Interface RagBackend 7 method, sehingga agent identik untuk RAGFlow & LightRAG", ic.scale]];
  cards.forEach(([t, d, im], i) => {
    const x = 0.6 + i * 4.15;
    circleIcon(s, im, x, 4.75, 0.7, HEX.amber, "card" + i);
    s.addText(t, { x: x + 0.85, y: 4.72, w: 3.1, h: 0.4, fontSize: 16, bold: true, color: HEX.teal, isTextBox: true, margin: 0 });
    s.addText(d, { x: x + 0.85, y: 5.12, w: 3.1, h: 1.5, fontSize: 13, color: HEX.ink, valign: "top", isTextBox: true, margin: 0 });
  });
  s.addNotes("Di ADK saya menyusun satu orchestrator, librarian, dengan empat sub-agent. Mode-nya dipilih sesuai kebutuhan: research_agent memakai chat agar bisa diskusi multi-turn, catalog dan compare memakai task, dan ingest memakai single_turn. Proses yang langkahnya selalu sama dibuat sebagai workflow graph. Untuk compare saya memakai routing dan parallel_worker, sehingga dua dokumen atau lebih diambil buktinya secara paralel.");

  // ---------- 4. Demo ----------
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Google ADK" });
  s.addText("Demo: shortcut chat dan jejak eksekusi di adk web", { placeholder: "title" });
  s.addImage({ path: path.join(IMG, "adk-web-bahas-trace.png"), x: 0.6, y: 1.45, w: 7.9, h: 4.94, objectName: "trace" });
  const sc = [["/dataset", "daftar koleksi & status"], ["/cari <kata>", "jawaban + kutipan halaman"], ["/bahas <dok>", "ringkas + diskusi lanjut"], ["/bandingkan A vs B", "file ↔ file · dataset ↔ dataset"], ["/upload", "lampirkan file → tersimpan"]];
  sc.forEach(([k, v], i) => {
    s.addText(k, { x: 8.85, y: 1.5 + i * 0.95, w: 3.9, h: 0.4, fontSize: 16, bold: true, color: HEX.teal, fontFace: "Courier New", isTextBox: true, margin: 0 });
    s.addText(v, { x: 8.85, y: 1.9 + i * 0.95, w: 3.9, h: 0.4, fontSize: 13, color: HEX.gray, isTextBox: true, margin: 0 });
  });
  s.addText("adk eval: 4/4 kasus routing lulus", { x: 8.85, y: 6.35, w: 3.9, h: 0.4, fontSize: 14, bold: true, color: HEX.rust, isTextBox: true, margin: 0 });
  s.addNotes("Ini tampilan adk web. Contohnya, ketik /bahas permenpan 38: librarian mentransfer ke research_agent, lalu memanggil read_document, dan semuanya terlihat di tab Trace. Shortcut-nya dikenali lewat instruksi, jadi tetap jalan di UI mana pun. Perilaku routing ini juga dikunci dengan adk eval, dan keempat kasusnya lulus.");

  // ---------- 5. Hasil ----------
  pres.addSection({ title: "Hasil" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Hasil" });
  const totalRF = score("ragflow"), totalLR = score("lightrag");
  s.addText("RAGFlow vs LightRAG: 10 pertanyaan, agent & LLM sama", { placeholder: "title" });
  s.addChart(pres.charts.BAR, [
    { name: "RAGFlow", labels: TYPES.map((t) => TYPE_LABEL[t]), values: TYPES.map((t) => +score("ragflow", t).toFixed(2)) },
    { name: "LightRAG", labels: TYPES.map((t) => TYPE_LABEL[t]), values: TYPES.map((t) => +score("lightrag", t).toFixed(2)) },
  ], {
    x: 0.6, y: 1.95, w: 7.4, h: 4.75, barDir: "col", barGrouping: "clustered", chartColors: [HEX.teal, HEX.amber],
    showTitle: false, layout: { x: 0.08, y: 0.1, w: 0.9, h: 0.72 },
    showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 12, dataLabelColor: HEX.ink, dataLabelFontFace: "+mn-lt", dataLabelFormatCode: "0.00",
    valAxisMinVal: 0, valAxisMaxVal: 5, valAxisMajorUnit: 1, valAxisLabelColor: HEX.gray, catAxisLabelColor: HEX.ink, catAxisLabelFontSize: 13,
    valAxisLabelFontFace: "+mn-lt", catAxisLabelFontFace: "+mn-lt",
    valGridLine: { color: "D9E3E2", size: 0.5 }, catGridLine: { style: "none" },
    showLegend: true, legendPos: "b", legendFontSize: 12, legendFontFace: "+mn-lt", legendColor: HEX.ink,
  });
  s.addText("Skor rata-rata per jenis pertanyaan (1–5, LLM-judge)", { x: 0.6, y: 1.45, w: 7.4, h: 0.4, fontSize: 14, color: HEX.ink, isTextBox: true, margin: 0 });
  const stat = (x, y, big, label, color) => {
    s.addText(big, { x, y, w: 2.3, h: 0.85, fontSize: 40, bold: true, color, fontFace: THEME.headFontFace, isTextBox: true, margin: 0 });
    const lines = [].concat(label).map((t, i, arr) => ({ text: t, options: { breakLine: i < arr.length - 1 } }));
    s.addText(lines, { x, y: y + 0.85, w: 2.3, h: 0.6, fontSize: 12, color: HEX.gray, valign: "top", isTextBox: true, margin: 0 });
  };
  const id = (x, d) => x.toFixed(d).replace(".", ",");
  stat(8.4, 1.5, id(totalRF, 2), "RAGFlow, skor total", HEX.teal);
  stat(10.6, 1.5, id(totalLR, 2), "LightRAG, skor total", HEX.amber);
  stat(8.4, 3.1, id(med("ragflow"), 0) + " s", ["RAGFlow, median latensi", `rata-rata ${id(lat("ragflow"), 0)} s`], HEX.teal);
  stat(10.6, 3.1, id(med("lightrag"), 0) + " s", ["LightRAG, median latensi", `rata-rata ${id(lat("lightrag"), 0)} s (1 outlier)`], HEX.amber);
  s.addText(TAKEAWAY(), { x: 8.4, y: 4.9, w: 4.5, h: 1.8, fontSize: 13, color: HEX.ink, valign: "top", isTextBox: true, margin: 0 });
  s.addNotes(NOTES_RESULT());

  // ---------- 6. Penutup ----------
  pres.addSection({ title: "Penutup" });
  s = pres.addSlide({ masterName: "DARK", sectionTitle: "Penutup" });
  s.addText("Pelajaran & langkah berikutnya", { x: 0.8, y: 0.6, w: 11.7, h: 0.9, fontSize: 36, bold: true, color: "FFFFFF", fontFace: THEME.headFontFace, isTextBox: true, margin: 0 });
  const items = [
    [ic.bulb, "Workflow untuk langkah tetap, LLM untuk keputusan", "Pipeline ingest & compare tanpa LLM: murah, cepat, bisa dites"],
    [ic.scale, "Uji ke server asli, bukan mock", "Bug versi RAGFlow v1.0 dan LightRAG 1.5.7 hanya ketahuan lewat integration test"],
    [ic.layers, "Sumber daya laptop itu nyata", "DeepDoc + Elasticsearch butuh RAM besar: satu stack berat dalam satu waktu"],
    [ic.rocket, "Berikutnya: deploy ke Vertex AI", "Agent Engine / Cloud Run, session persisten, eval di CI"],
  ];
  items.forEach(([im, t, d], i) => {
    const y = 1.85 + i * 1.25;
    circleIcon(s, im, 0.8, y, 0.75, HEX.amber, "end" + i);
    s.addText(t, { x: 1.8, y: y - 0.02, w: 10.5, h: 0.42, fontSize: 20, bold: true, color: "FFFFFF", isTextBox: true, margin: 0 });
    s.addText(d, { x: 1.8, y: y + 0.4, w: 10.5, h: 0.4, fontSize: 14, color: HEX.ice, isTextBox: true, margin: 0 });
  });
  s.addNotes("Tiga pelajaran utama. Pertama, pakai workflow untuk langkah yang selalu sama, dan LLM hanya untuk keputusan. Kedua, selalu uji ke server asli, karena bug versi baru ketahuan di integration test. Ketiga, sumber daya laptop terbatas, jadi jalankan satu stack berat dalam satu waktu. Langkah berikutnya: deploy ke Vertex AI. Kodenya juga sudah berupa starter kit untuk produk berikutnya. Terima kasih.");

  const out = path.join(ROOT, "laporan", "Presentasi-RAGFlow-vs-LightRAG.pptx");
  await pres.writeFile({ fileName: out });
  const { applyTheme } = require(process.env.PPTX_SKILL + "/scripts/apply_theme.js");
  await applyTheme(out, THEME);
  console.log("wrote", out);
})();

function TAKEAWAY() {
  const by = (t) => [score("ragflow", t), score("lightrag", t)];
  const parts = TYPES.map((t) => {
    const [a, b] = by(t);
    const w = Math.abs(a - b) < 0.05 ? "seri" : a > b ? "RAGFlow unggul" : "LightRAG unggul";
    return `${TYPE_LABEL[t]}: ${w}`;
  });
  return parts.join(" · ") + ". Detail per pertanyaan ada di eval/results.";
}

function NOTES_RESULT() {
  return `Saya membandingkan dengan adil: agent, prompt, LLM, dan embedding sama, hanya backend retrieval yang berbeda. Ada 10 pertanyaan dalam tiga jenis. Skor total RAGFlow ${score("ragflow").toFixed(2)} dan LightRAG ${score("lightrag").toFixed(2)} dari 5. ${TAKEAWAY()} Median latensi RAGFlow ${med("ragflow").toFixed(0)} detik dan LightRAG ${med("lightrag").toFixed(0)} detik; LightRAG lebih lambat karena memanggil LLM untuk ekstraksi kata kunci di setiap query. Ini masih PoC dengan 10 pertanyaan, jadi indikatif, bukan kesimpulan statistik.`;
}
