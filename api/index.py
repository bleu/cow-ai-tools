"""
Vercel serverless entry for the chat API (Quart ASGI app).
Vercel serves this at /api, so requests are /api/up and /api/predict.
We strip the /api prefix so the Quart app sees /up and /predict.
Requires local packages on PYTHONPATH; see docs/deploy-vercel.md.
"""
from pathlib import Path
import sys

# Add monorepo packages so "from op_app.api import app" works
_root = Path(__file__).resolve().parent.parent
for p in ("pkg/op-core", "pkg/op-artifacts", "pkg/op-data", "pkg/op-brains", "pkg/cow-brains", "pkg/op-app"):
    _path = _root / p
    if _path.exists() and str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from op_app.api import app as _quart_app


async def _strip_api_prefix(scope, receive, send):
    if scope.get("type") == "http" and scope.get("path", "").startswith("/api"):
        scope = dict(scope)
        scope["path"] = scope["path"][4:] or "/"
    await _quart_app(scope, receive, send)


# Vercel Python runtime uses the ASGI app when the variable is named "app"
app = _strip_api_prefix
