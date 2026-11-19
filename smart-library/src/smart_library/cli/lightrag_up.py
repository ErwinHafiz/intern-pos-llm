"""`uv run lightrag-up`: jalankan 1 LightRAG Server per dataset (LIGHTRAG_WORKSPACES).

LightRAG Server v1.5 belum bisa memilih workspace per request, jadi tiap dataset
punya proses + port + WebUI sendiri. Konfigurasi LLM/embedding diambil dari .env utama.
"""

import os
import re
import subprocess
import sys
import time
from collections.abc import Mapping
from urllib.parse import urlparse

from smart_library.config import PROJECT_ROOT, Settings, load_settings

EMBEDDING_DIMS = {"text-embedding-3-small": "1536", "text-embedding-3-large": "3072"}


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def server_specs(settings: Settings, env: Mapping[str, str]) -> list[dict]:
    embedding = env.get("EMBEDDING_DEPLOYMENT") or "text-embedding-3-small"
    llm = env.get("LIGHTRAG_LLM_DEPLOYMENT") or settings.llm_model.split("/", 1)[-1]
    server_env = {
        "LLM_BINDING": "openai",  # endpoint Azure /openai/v1 kompatibel OpenAI
        "LLM_BINDING_HOST": settings.llm_api_base,
        "LLM_BINDING_API_KEY": settings.llm_api_key,
        "LLM_MODEL": llm,
        "EMBEDDING_BINDING": "openai",
        "EMBEDDING_BINDING_HOST": settings.llm_api_base,
        "EMBEDDING_BINDING_API_KEY": settings.llm_api_key,
        "EMBEDDING_MODEL": embedding,
        "EMBEDDING_DIM": EMBEDDING_DIMS.get(embedding, "1536"),
        "PYTHONUTF8": "1",  # konsol Windows cp1252 tidak bisa mencetak banner LightRAG
        "LOG_DIR": str(PROJECT_ROOT / "data" / "lightrag" / "logs"),
        # parser LightRAG 1.5.7 mencari file sumber lewat env INPUT_DIR, bukan --input-dir
        "INPUT_DIR": str(PROJECT_ROOT / "data" / "lightrag" / "inputs"),
    }
    if settings.lightrag_api_key:
        server_env["LIGHTRAG_API_KEY"] = settings.lightrag_api_key
    specs = []
    for name, url in settings.lightrag_workspaces.items():
        ws, port = slugify(name), str(urlparse(url).port or 9621)
        work = PROJECT_ROOT / "data" / "lightrag"
        args = ["--host", "127.0.0.1", "--port", port, "--workspace", ws,
                "--working-dir", str(work), "--input-dir", server_env["INPUT_DIR"]]  # server menambah /<ws> sendiri
        specs.append({"name": name, "workspace": ws, "port": port, "url": url, "args": args, "env": server_env})
    return specs


def main() -> None:
    settings = load_settings()
    specs = server_specs(settings, os.environ)
    if not specs:
        sys.exit("LIGHTRAG_WORKSPACES kosong di .env")
    log_dir = PROJECT_ROOT / "data" / "lightrag" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    procs = []
    for s in specs:
        log = open(log_dir / f"{s['workspace']}.log", "a", encoding="utf-8")
        cmd = [sys.executable, "-m", "lightrag.api.lightrag_server", *s["args"]]
        procs.append(subprocess.Popen(cmd, env={**os.environ, **s["env"]}, stdout=log, stderr=subprocess.STDOUT))
        print(f"[{s['name']}] WebUI {s['url']}/webui  (log: data/lightrag/logs/{s['workspace']}.log)")
    print("Ctrl+C untuk berhenti.")
    try:
        while all(p.poll() is None for p in procs):
            time.sleep(1)
        print("Salah satu server berhenti, cek log di data/lightrag/logs/")
    except KeyboardInterrupt:
        pass
    finally:
        for p in procs:
            p.terminate()


if __name__ == "__main__":
    main()
