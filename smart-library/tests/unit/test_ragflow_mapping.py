import pytest

from smart_library.backends.ragflow_backend import chunk_location, map_status


@pytest.mark.parametrize("run,progress,expected", [
    ("DONE", 1.0, "DONE"), ("3", 1.0, "DONE"),
    ("0", 1.0, "DONE"),          # server v1.0: run tetap "0" walau parsing selesai
    ("RUNNING", 0.4, "RUNNING"), ("1", 0.0, "RUNNING"), ("0", 0.5, "RUNNING"),
    ("FAIL", 0.0, "FAIL"), ("4", 0.0, "FAIL"), ("CANCEL", 0.2, "FAIL"), ("2", 0.0, "FAIL"), ("0", -1.0, "FAIL"),
    ("UNSTART", 0.0, "PENDING"), ("0", 0.0, "PENDING"),
])
def test_map_status(run, progress, expected):
    assert map_status(run, progress) == expected


def test_chunk_location_page():
    assert chunk_location([[90, 72, 538, 48, 876]]) == "hlm. 90"


def test_chunk_location_empty():
    assert chunk_location([]) is None
    assert chunk_location(None) is None


def test_invalid_json_response_is_not_reported_as_unreachable():
    import requests

    from smart_library.backends.base import BackendError
    from smart_library.backends.ragflow_backend import RagflowBackend

    b = RagflowBackend("http://localhost:1", "x")

    def boom(**kw):
        raise requests.exceptions.JSONDecodeError("Expecting value", "<html>502</html>", 0)

    b.rag.list_datasets = boom
    with pytest.raises(BackendError) as e:
        b.list_datasets()
    assert "respons tidak valid" in str(e.value) and "tidak bisa dihubungi" not in str(e.value)
