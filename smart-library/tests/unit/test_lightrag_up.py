from smart_library.cli.lightrag_up import server_specs, slugify
from smart_library.config import load_settings

ENV = {
    "LLM_MODEL": "openai/gpt-5.1", "LLM_API_BASE": "https://x/openai/v1", "LLM_API_KEY": "k",
    "LIGHTRAG_WORKSPACES": "Regulasi Digital ID=http://localhost:9621,Riset RAG=http://localhost:9622",
    "EMBEDDING_DEPLOYMENT": "text-embedding-3-small", "LIGHTRAG_LLM_DEPLOYMENT": "gpt-4.1-mini",
}


def test_slugify():
    assert slugify("Regulasi Digital ID") == "regulasi_digital_id"


def test_server_specs_one_per_workspace():
    specs = server_specs(load_settings(ENV), ENV)
    assert [(s["workspace"], s["port"]) for s in specs] == [("regulasi_digital_id", "9621"), ("riset_rag", "9622")]
    env = specs[0]["env"]
    assert env["LLM_BINDING"] == "openai" and env["LLM_MODEL"] == "gpt-4.1-mini"
    assert env["EMBEDDING_MODEL"] == "text-embedding-3-small" and env["EMBEDDING_DIM"] == "1536"
    assert env["LLM_BINDING_HOST"] == "https://x/openai/v1" and env["EMBEDDING_BINDING_API_KEY"] == "k"
    assert "--workspace" in specs[0]["args"] and "regulasi_digital_id" in specs[0]["args"]
    # server sendiri menambahkan /<workspace> ke input-dir, jadi yang dikirim direktori dasar
    input_dir = specs[0]["args"][specs[0]["args"].index("--input-dir") + 1]
    assert input_dir.replace("\\", "/").endswith("data/lightrag/inputs")
    # parser LightRAG 1.5.7 membaca env INPUT_DIR (bukan --input-dir) saat mencari file sumber
    assert env["INPUT_DIR"] == input_dir
