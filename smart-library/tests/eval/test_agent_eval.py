"""adk eval terhadap agent RAGFlow asli (Azure + RAGFlow hidup). Jalankan: uv run pytest -m eval

Kasus direkam dari sesi asli lewat tab Eval adk web (lihat catatan-belajar/07-evaluasi.md).
- tool_trajectory_avg_score (IN_ORDER, ignore_args): shortcut harus sampai ke sub-agent & tool yang benar.
- response_match_score (ROUGE-1) 0.5: kata-kata jawaban LLM bervariasi; trajektori adalah asersi utama.
"""

from pathlib import Path

import pytest
from google.adk.evaluation.agent_evaluator import AgentEvaluator

from smart_library.app import build_app
from smart_library.backends.ragflow_backend import RagflowBackend

pytestmark = pytest.mark.eval


async def test_routing_evalset():
    await AgentEvaluator.evaluate(
        agent_module=build_app(RagflowBackend.from_env()),
        eval_dataset_file_path_or_dir=str(Path(__file__).parent / "library_ragflow"),
    )
