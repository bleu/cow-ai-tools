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


def _path_from_query(scope):
    """Restore path from rewrite query param (Vercel: /api/up -> /api?path=up)."""
    qs = scope.get("query_string") or b""
    if isinstance(qs, bytes):
        qs = qs.decode("utf-8", "replace")
    for part in qs.split("&"):
        if part.startswith("path="):
            sub = part[5:].strip()
            if sub:
                return "/api/" + sub
    return None


async def _strip_api_prefix(scope, receive, send):
    if scope.get("type") != "http":
        await _quart_app(scope, receive, send)
        return
    scope = dict(scope)
    path = scope.get("path") or ""
    # Vercel rewrites send /api/up and /api/predict to /api?path=up|predict
    from_rewrite = _path_from_query(scope)
    if from_rewrite:
        path = from_rewrite
    if path.startswith("/api"):
        scope["path"] = path[4:] or "/"
    await _quart_app(scope, receive, send)


# Vercel Python runtime uses the ASGI app when the variable is named "app"
app = _strip_api_prefix
