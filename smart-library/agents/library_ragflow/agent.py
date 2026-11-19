from smart_library.app import build_app
from smart_library.backends.ragflow_backend import RagflowBackend

app = build_app(RagflowBackend.from_env())
