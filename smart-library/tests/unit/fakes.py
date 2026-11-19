"""FakeBackend: HANYA untuk tests/unit. Produk, seed, eval & integration selalu pakai backend asli."""

from smart_library.backends.base import BackendError, Chunk, Dataset, Document


class FakeBackend:
    name = "fake"

    def __init__(self, datasets: dict[str, list[tuple[str, str]]], parse_result: str = "DONE"):
        self.down = False
        self.parse_result = parse_result
        self._datasets = {f"ds{i}": Dataset(f"ds{i}", n) for i, n in enumerate(datasets)}
        self._docs: dict[str, tuple[Document, str]] = {}
        for ds in self._datasets.values():
            for name, text in datasets[ds.name]:
                self._add(ds.id, name, text, "DONE")

    def _add(self, dataset_id, name, text, status):
        doc = Document(f"doc{len(self._docs)}", name, dataset_id, status)
        self._docs[doc.id] = (doc, text)
        return doc

    def _check(self):
        if self.down:
            raise BackendError("RAGFlow tidak bisa dihubungi di http://localhost — jalankan `docker compose up -d`")

    def list_datasets(self):
        self._check()
        for ds in self._datasets.values():
            ds.doc_count = sum(d.dataset_id == ds.id for d, _ in self._docs.values())
        return list(self._datasets.values())

    def list_documents(self, dataset_id):
        self._check()
        return [d for d, _ in self._docs.values() if d.dataset_id == dataset_id]

    def ensure_dataset(self, name, description=""):
        self._check()
        for ds in self._datasets.values():
            if ds.name == name:
                return ds
        ds = Dataset(f"ds{len(self._datasets)}", name, description)
        self._datasets[ds.id] = ds
        return ds

    def upload(self, dataset_id, filename, data):
        self._check()
        if any(d.name == filename and d.dataset_id == dataset_id for d, _ in self._docs.values()):
            raise BackendError(f"'{filename}' sudah ada di dataset ini")
        return self._add(dataset_id, filename, data.decode("utf-8", "ignore"), "PENDING")

    def start_parse(self, dataset_id, doc_ids):
        self._check()
        for i in doc_ids:
            self._docs[i][0].status = self.parse_result

    def parse_status(self, dataset_id, doc_ids):
        self._check()
        return {i: self._docs[i][0].status for i in doc_ids}

    def retrieve(self, query, *, dataset_ids=None, document_ids=None, top_k=8):
        self._check()
        words = set(query.lower().split())
        out = []
        for doc, text in self._docs.values():
            if dataset_ids and doc.dataset_id not in dataset_ids:
                continue
            if document_ids and doc.id not in document_ids:
                continue
            score = len(words & set(text.lower().split()))
            if score:
                out.append(Chunk(text, doc.name, self._datasets[doc.dataset_id].name, float(score), "hlm. 1"))
        return sorted(out, key=lambda c: -c.score)[:top_k]
