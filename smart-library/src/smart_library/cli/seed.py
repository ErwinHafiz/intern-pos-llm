"""`uv run seed [--backend ragflow|lightrag|all] [--dry-run]`

Unduh dokumen publik asli (data/sources.yaml) → buat dataset → upload → parse → tunggu.
Idempoten: file yang sudah terunduh / dokumen yang sudah ada di backend dilewati.
"""

import argparse
import sys
import time
from pathlib import Path

import httpx
import yaml

from smart_library.backends.base import BackendError, RagBackend
from smart_library.config import PROJECT_ROOT

SOURCES = PROJECT_ROOT / "data" / "sources.yaml"
DOWNLOADS = PROJECT_ROOT / "data" / "downloads"
MAGIC = {"pdf": b"%PDF", "docx": b"PK", "xlsx": b"PK", "pptx": b"PK"}
BROWSER_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"


class SeedError(Exception):
    pass


def load_sources(path: Path = SOURCES) -> list[dict]:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))["datasets"]


def looks_valid(path: Path, fmt: str) -> bool:
    """Cegah halaman HTML error/captcha tersimpan sebagai .pdf/.docx/.csv."""
    if not path.exists() or path.stat().st_size == 0:
        return False
    head = path.read_bytes()[:16]
    if fmt in MAGIC:
        return head.startswith(MAGIC[fmt])
    return not head.lstrip().startswith(b"<")


def download(doc: dict, dest: Path) -> Path:
    target = Path(dest) / doc["filename"]
    if looks_valid(target, doc["format"]):
        return target
    manual = (f"Gagal mengunduh '{doc['filename']}'. Unduh manual dari {doc.get('page') or doc['url']} "
              f"lalu simpan sebagai {target}")
    try:
        r = httpx.get(doc["url"], headers={"User-Agent": BROWSER_UA}, follow_redirects=True, timeout=120)
        r.raise_for_status()
    except httpx.HTTPError as e:
        raise SeedError(f"{manual} ({type(e).__name__})") from e
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(r.content)
    if not looks_valid(target, doc["format"]):
        target.unlink()
        raise SeedError(f"{manual} (server tidak mengirim file {doc['format']} yang valid)")
    return target


def seed_backend(backend: RagBackend, sources: list[dict], dl_dir: Path,
                 poll_interval: float = 10, timeout: float = 3600) -> dict[str, str]:
    pending: dict[str, tuple[str, str]] = {}  # doc_id -> (dataset_id, nama)
    for ds_src in sources:
        ds = backend.ensure_dataset(ds_src["name"], ds_src.get("description", ""))
        existing = {d.name for d in backend.list_documents(ds.id)}
        for doc in ds_src["documents"]:
            if doc["filename"] in existing:
                print(f"  = {doc['filename']} (sudah ada)")
                continue
            uploaded = backend.upload(ds.id, doc["filename"], (Path(dl_dir) / doc["filename"]).read_bytes())
            backend.start_parse(ds.id, [uploaded.id])
            pending[uploaded.id] = (ds.id, doc["filename"])
            print(f"  + {doc['filename']} diupload, parsing dimulai")
    results: dict[str, str] = {}
    deadline = time.monotonic() + timeout
    while pending and time.monotonic() < deadline:
        for doc_id, (ds_id, name) in list(pending.items()):
            try:
                status = backend.parse_status(ds_id, [doc_id])[doc_id]
            except BackendError as e:  # gangguan sesaat saat polling; parsing tetap jalan di server
                print(f"  ! cek status {name} gagal, dicoba lagi: {e}")
                continue
            if status in ("DONE", "FAIL"):
                results[name] = status
                pending.pop(doc_id)
                print(f"  {'✓' if status == 'DONE' else '✗'} {name}: {status}")
        if pending:
            time.sleep(poll_interval)
    results.update({name: "RUNNING (timeout, cek UI backend)" for _, name in pending.values()})
    return results


def _backends(choice: str) -> list[RagBackend]:
    from smart_library.backends.ragflow_backend import RagflowBackend

    out = []
    if choice in ("ragflow", "all"):
        out.append(RagflowBackend.from_env())
    if choice in ("lightrag", "all"):
        from smart_library.backends.lightrag_backend import LightragBackend

        out.append(LightragBackend.from_env())
    return out


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="Seed koleksi dokumen asli ke backend RAG")
    p.add_argument("--backend", choices=["ragflow", "lightrag", "all"], default="ragflow")
    p.add_argument("--dry-run", action="store_true", help="hanya unduh & verifikasi file")
    args = p.parse_args()

    sources = load_sources()
    failed = []
    for doc in (d for ds in sources for d in ds["documents"]):
        try:
            print(f"✓ {download(doc, DOWNLOADS).name}")
        except SeedError as e:
            failed.append(str(e))
    if failed:
        sys.exit("\n".join(["File berikut perlu diunduh manual:", *failed]))
    if args.dry_run:
        return
    for backend in _backends(args.backend):
        print(f"\n== {backend.name} ==")
        try:
            results = seed_backend(backend, sources, DOWNLOADS)
        except BackendError as e:
            sys.exit(str(e))
        bad = {k: v for k, v in results.items() if v != "DONE"}
        print(f"Selesai: {len(results) - len(bad)} dokumen baru siap" + (f", bermasalah: {bad}" if bad else ""))


if __name__ == "__main__":
    main()
