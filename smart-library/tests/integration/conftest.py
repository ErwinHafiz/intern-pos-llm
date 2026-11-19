from pathlib import Path

import pytest

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


@pytest.fixture
def sample_bytes() -> bytes:
    return (FIXTURES / "sample.md").read_bytes()
