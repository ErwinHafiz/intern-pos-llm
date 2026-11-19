from smart_library.app import build_app
from smart_library.backends.lightrag_backend import LightragBackend

app = build_app(LightragBackend.from_env())
