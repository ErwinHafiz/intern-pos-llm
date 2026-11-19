import pytest

from smart_library.config import load_settings

MIN = {"LLM_MODEL": "openai/gpt-5.1", "LLM_API_BASE": "https://x/openai/v1", "LLM_API_KEY": "k"}


def test_parse_workspaces():
    s = load_settings({
        "LIGHTRAG_WORKSPACES": "Regulasi Digital ID=http://localhost:9621,Riset RAG=http://localhost:9622",
        **MIN,
    })
    assert s.lightrag_workspaces == {
        "Regulasi Digital ID": "http://localhost:9621",
        "Riset RAG": "http://localhost:9622",
    }


def test_missing_required_raises_clear_error():
    with pytest.raises(ValueError, match="LLM_MODEL"):
        load_settings({})


def test_optional_defaults():
    s = load_settings(MIN)
    assert s.ragflow_base_url == "http://localhost:9380"
    assert s.lightrag_workspaces == {}
