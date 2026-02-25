"""
Minimal chat API: health check + /predict.
Uses cow_brains when PROJECT=cow (CoW Protocol), op_brains when PROJECT=optimism or unset (Optimism).
"""
import os
import time
from pathlib import Path
from functools import wraps

# Load .env from pkg/op-app so GOOGLE_API_KEY etc. are set before any brain imports
_env_file = Path(__file__).resolve().parent.parent / ".env"
if _env_file.is_file():
    from dotenv import load_dotenv
    load_dotenv(_env_file)

from quart import Quart, request, jsonify
from quart_cors import cors

_PROJECT = (os.getenv("PROJECT") or os.getenv("USE_COW", "false")).strip().lower()
if _PROJECT in ("cow", "true", "1", "yes"):
    from cow_brains import process_question
    from op_brains.exceptions import UnsupportedVectorstoreError  # reuse
else:
    from op_brains.exceptions import UnsupportedVectorstoreError
    from op_brains.chat.utils import process_question

# Log env state at startup (no secrets). Railway injects vars at container start; redeploy after changing them.
def _has_google_key():
    key = (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or "").strip()
    if key:
        return True
    for name in ("GOOGLE_API_KEY_FILE", "GEMINI_API_KEY_FILE"):
        path = os.getenv(name)
        if path and os.path.isfile(path):
            with open(path) as f:
                if (f.read() or "").strip():
                    return True
    return False

if _PROJECT in ("cow", "true", "1", "yes"):
    if not _has_google_key():
        print("WARNING: Gemini API key not set. Set GOOGLE_API_KEY or GEMINI_API_KEY and redeploy.", flush=True)
    else:
        print("Gemini API key is set.", flush=True)

app = Quart(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_API_SECRET_KEY", "dev-secret")
app = cors(app)


def handle_question(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        data = await request.get_json()
        if data is not None:
            question = data.get("question")
            memory = data.get("memory", [])
        else:
            question = None
            memory = []

        if not question:
            return jsonify({"error": "No question provided"}), 400

        return await func(question, memory, *args, **kwargs)

    return wrapper


@app.errorhandler(Exception)
def handle_exception(e):
    if isinstance(e, UnsupportedVectorstoreError):
        return jsonify({"error": str(e)}), 400
    return jsonify({"error": "An unexpected error occurred during prediction"}), 500


@app.route("/up", methods=["GET"])
async def health_check():
    return jsonify({"status": "healthy", "service": "chat-api"}), 200


@app.route("/predict", methods=["POST"])
@handle_question
async def predict(question, memory):
    t0 = time.perf_counter()
    verbose = os.getenv("COW_VERBOSE", "").strip().lower() in ("1", "true", "yes")
    result = await process_question(question, memory, verbose=verbose)
    elapsed = time.perf_counter() - t0
    if result.get("error"):
        print(f"[predict] question={question[:50]}... error in {elapsed:.2f}s: {result.get('error', '')[:60]}", flush=True)
        return jsonify(result), 503
    print(f"[predict] question={question[:50]}... ok in {elapsed:.2f}s")
    return jsonify(result), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
