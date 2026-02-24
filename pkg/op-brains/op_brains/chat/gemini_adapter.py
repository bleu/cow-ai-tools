"""
Adapter for Google Gemini (gemini-2.0-flash and embeddings) using the official google-generativeai SDK.
- Chat: LangChain-compatible with_structured_output(...) and invoke(prompt).
- Embeddings: LangChain-compatible embed_documents / embed_query (same GOOGLE_API_KEY).
Set GOOGLE_API_KEY in the environment.
Note: The deprecated SDK does not support request timeout; we wrap generate_content in a thread timeout.
"""
import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Type, TypeVar, List

import google.generativeai as genai

try:
    from google.api_core.exceptions import ResourceExhausted
except ImportError:
    ResourceExhausted = None  # type: ignore[misc, assignment]

T = TypeVar("T")

# Configure once when module is first used for Gemini
_configured = False


def _ensure_configured():
    global _configured
    if _configured:
        return
    key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not key:
        raise ValueError(
            "Set GOOGLE_API_KEY (or GEMINI_API_KEY) in the environment to use Gemini."
        )
    genai.configure(api_key=key)
    _configured = True


def _schema_to_json_schema(schema_class: Type[T]) -> dict:
    """Get JSON schema from Pydantic model (v1 or v2)."""
    if hasattr(schema_class, "schema"):
        return schema_class.schema()
    return schema_class.model_json_schema()


def _repair_json_string_quotes(text: str) -> str:
    """Try to fix JSON with unescaped double quotes inside string values (e.g. "sellToken" inside a string -> \\"sellToken\\")."""
    result = []
    i = 0
    in_string = False
    after_backslash = False
    while i < len(text):
        c = text[i]
        if in_string:
            if after_backslash:
                result.append(c)
                after_backslash = False
            elif c == "\\":
                result.append(c)
                after_backslash = True
            elif c == '"':
                # Peek ahead: next non-space char , } ] : means this " closes the string
                j = i + 1
                while j < len(text) and text[j] in " \t\n\r":
                    j += 1
                next_char = text[j] if j < len(text) else ""
                if next_char in ",}:]":
                    result.append(c)
                    in_string = False
                else:
                    result.append("\\")
                    result.append(c)
            else:
                result.append(c)
            i += 1
            continue
        if c == '"':
            result.append(c)
            in_string = True
            i += 1
            continue
        result.append(c)
        i += 1
    return "".join(result)


# Kwargs that belong in GenerationConfig, not in GenerativeModel.__init__
_GENERATION_KEYS = {"temperature", "max_tokens", "max_retries", "timeout"}


class _StructuredGemini:
    """Wrapper returned by with_structured_output; has invoke() that returns the Pydantic model instance."""

    def __init__(self, model_name: str, schema_class: Type[T], **model_kwargs):
        _ensure_configured()
        gen_config = {k: v for k, v in model_kwargs.items() if k in _GENERATION_KEYS}
        model_only = {k: v for k, v in model_kwargs.items() if k not in _GENERATION_KEYS}
        self._model = genai.GenerativeModel(model_name, **model_only)
        self._schema_class = schema_class
        self._gen_config = gen_config

    def invoke(self, prompt: str) -> T:
        schema = _schema_to_json_schema(self._schema_class)
        schema_str = json.dumps(schema, indent=2)
        full_prompt = (
            f"{prompt}\n\n"
            "You must respond with a single valid JSON object (no markdown, no code block) "
            f"that conforms to this schema:\n{schema_str}\n\n"
            "Important: Inside any string value, escape double quotes with a backslash (e.g. \\\"). "
            "For example write \\\"sellToken\\\" not \"sellToken\" inside a string so the JSON stays valid."
        )
        timeout_sec = self._gen_config.get("timeout", 60)
        max_retries = 3
        base_delay = 2.0

        def _one_call():
            try:
                config = genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=self._gen_config.get("temperature", 0.0),
                    max_output_tokens=self._gen_config.get("max_tokens", 1024),
                )
                return self._model.generate_content(full_prompt, generation_config=config)
            except Exception:
                return self._model.generate_content(full_prompt)

        def _generate():
            last_exc = None
            for attempt in range(max_retries + 1):
                try:
                    return _one_call()
                except Exception as e:
                    is_429 = ResourceExhausted is not None and isinstance(e, ResourceExhausted)
                    if is_429 and attempt < max_retries:
                        delay = base_delay * (2**attempt)
                        time.sleep(delay)
                        last_exc = e
                        continue
                    raise
            if last_exc is not None:
                raise last_exc
        # Allow extra time for 429 retry backoff (e.g. 2+4+8s)
        total_timeout = timeout_sec + sum(base_delay * (2**i) for i in range(max_retries))
        with ThreadPoolExecutor(max_workers=1) as ex:
            fut = ex.submit(_generate)
            try:
                response = fut.result(timeout=total_timeout)
            except FuturesTimeoutError:
                raise TimeoutError(f"Gemini generate_content timed out after {total_timeout}s")
        text = (response.text or "").strip()
        if "```json" in text:
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
        elif "```" in text:
            text = re.sub(r"^```\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
        data = None
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            import logging
            log = logging.getLogger(__name__)
            log.warning("Gemini JSON decode failed: %s. Raw (truncated): %s", e, text[:500])
            repaired = _repair_json_string_quotes(text)
            if repaired != text:
                try:
                    data = json.loads(repaired)
                except json.JSONDecodeError:
                    pass
            if data is None:
                try:
                    import json_repair
                    data = json_repair.loads(text)
                except Exception as repair_err:
                    log.warning("json_repair fallback failed: %s", repair_err)
                    raise e
        if not isinstance(data, dict):
            raise ValueError("Gemini response is not a JSON object")
        import logging as _log
        _adapter_log = _log.getLogger(__name__)
        # For Responder-like payloads, always build from scratch so raw keys like '"sellToken"' never reach Pydantic.
        # Use builder when schema has knowledge_summary OR when data looks like Responder (has knowledge_summary key).
        schema_fields = getattr(self._schema_class, "__fields__", None) or getattr(self._schema_class, "model_fields", {}) or {}
        schema_field_names = list(schema_fields.keys()) if schema_fields else []
        use_builder = "knowledge_summary" in schema_fields or "knowledge_summary" in data
        _adapter_log.debug(
            "Adapter payload path: use_builder=%s schema_fields=%s raw_keys=%s",
            use_builder, schema_field_names, list(data.keys()),
        )
        if use_builder:
            data = _build_responder_payload(data)
            _adapter_log.debug("After _build_responder_payload: keys=%s", list(data.keys()))
        else:
            data = _remove_blacklisted_keys_recursive(data)
            allowed_top = set(schema_field_names) or set(data.keys())
            data = {k: v for k, v in data.items() if k in allowed_top}
        # Log any key that could trigger KeyError (e.g. "sellToken") so we can trace the bug
        def _all_keys(d, prefix=""):
            for k, v in (d.items() if isinstance(d, dict) else []):
                key_str = repr(k)
                if "selltoken" in key_str.lower() or "buytoken" in key_str.lower():
                    _adapter_log.warning("Dangerous key in payload before Pydantic: %s%s", prefix, key_str)
                if isinstance(v, dict):
                    _all_keys(v, prefix + repr(k) + ".")
                elif isinstance(v, list) and v and isinstance(v[0], dict):
                    for i, item in enumerate(v):
                        _all_keys(item, prefix + repr(k) + "[%s]." % i)
        _all_keys(data)
        try:
            return self._schema_class(**data)
        except Exception as e:
            import traceback
            _adapter_log.warning(
                "Gemini schema parse failed: %s %s. Keys passed: %s\nTraceback: %s",
                type(e).__name__, e, list(data.keys()) if isinstance(data, dict) else [], traceback.format_exc(),
            )
            raise


# Keys that Gemini sometimes adds (from API examples in context); remove them everywhere to avoid Pydantic KeyError
_BLACKLIST_KEYS = frozenset({
    '"sellToken"', '"buyToken"', "sellToken", "buyToken",
    "sellAmount", "buyAmount", "sellAmountBeforeFee", "buyAmountAfterFee",
    "validTo", "appData", "from", "kind", "receiver", "quoteId",
})


def _is_blacklisted_key(k) -> bool:
    """True if key should be removed (exact match or variant like quote-wrapped / Unicode)."""
    if k in _BLACKLIST_KEYS:
        return True
    if not isinstance(k, str):
        return False
    normalized = k.strip().strip("\"'\u201c\u201d\u2018\u2019").lower()
    if normalized in ("selltoken", "buytoken", "sellamount", "buyamount"):
        return True
    # Catch any key containing these tokens (e.g. '"sellToken"', 'sellToken', Unicode variants)
    if "selltoken" in normalized or "buytoken" in normalized:
        return True
    if "selltoken" in k.lower() or "buytoken" in k.lower():
        return True
    return False


def _remove_blacklisted_keys_recursive(obj):
    """Remove any blacklisted key from dicts at any nesting level (so Pydantic never sees e.g. \"sellToken\")."""
    if isinstance(obj, dict):
        return {
            k: _remove_blacklisted_keys_recursive(v)
            for k, v in obj.items()
            if not _is_blacklisted_key(k)
        }
    if isinstance(obj, list):
        return [_remove_blacklisted_keys_recursive(item) for item in obj]
    return obj


# Keys allowed in nested Responder objects (strip any extra keys from Gemini to avoid Pydantic KeyError)
_ANSWER_KEYS = {"answer", "url_supporting"}
_SEARCH_KEYS = {"user_knowledge", "questions", "keywords", "type_search"}
_CLAIM_KEYS = {"claim", "url_supporting"}
_RESPONDER_TOP_KEYS = {"knowledge_summary", "answer", "search"}


def _build_responder_payload(raw: dict) -> dict:
    """Build a clean payload by reading only known keys; no raw dict is passed to Pydantic so keys like \"sellToken\" never appear."""
    out = {}
    ks = raw.get("knowledge_summary")
    if isinstance(ks, list):
        out["knowledge_summary"] = []
        for item in ks:
            if isinstance(item, dict):
                out["knowledge_summary"].append({
                    "claim": str(item.get("claim", item.get("url_supporting", ""))),
                    "url_supporting": str(item.get("url_supporting", "")) if not isinstance(item.get("url_supporting"), list) else str((item.get("url_supporting") or [""])[0]),
                })
            else:
                out["knowledge_summary"].append({"claim": str(item), "url_supporting": ""})
    else:
        out["knowledge_summary"] = []
    a = raw.get("answer")
    if a is not None:
        if isinstance(a, str):
            out["answer"] = {"answer": a, "url_supporting": []}
        elif isinstance(a, dict):
            us = a.get("url_supporting")
            if not isinstance(us, list):
                us = []
            out["answer"] = {"answer": str(a.get("answer", "") or ""), "url_supporting": us}
    s = raw.get("search")
    if s is not None and isinstance(s, dict):
        out["search"] = {
            "user_knowledge": str(s.get("user_knowledge", "")),
            "questions": list(s.get("questions", [])) if isinstance(s.get("questions"), list) else [],
            "keywords": list(s.get("keywords", [])) if isinstance(s.get("keywords"), list) else [],
            "type_search": str(s.get("type_search", "factual")),
        }
    return out


def _strip_unknown_keys_recursive(obj, allowed: set):
    """Recursively keep only allowed keys in dicts. Removes e.g. \"sellToken\" at any nesting level."""
    if isinstance(obj, dict):
        return {k: _strip_unknown_keys_recursive(v, _next_allowed(k, allowed)) for k, v in obj.items() if k in allowed}
    if isinstance(obj, list):
        return [_strip_unknown_keys_recursive(item, _CLAIM_KEYS) for item in obj]
    return obj


def _next_allowed(key: str, current: set) -> set:
    if key == "answer":
        return _ANSWER_KEYS
    if key == "search":
        return _SEARCH_KEYS
    if key == "knowledge_summary":
        return _CLAIM_KEYS
    return current


def _normalize_responder_data(data: dict) -> dict:
    """Coerce Gemini response into shape expected by Responder schema. Recursively strip unknown keys (e.g. \"sellToken\") so Pydantic never sees them."""
    out = dict(data)
    # Normalize shape and types first
    if "answer" in out and out["answer"] is not None:
        a = out["answer"]
        if isinstance(a, str):
            out["answer"] = {"answer": a, "url_supporting": []}
        elif isinstance(a, dict):
            out["answer"] = {
                "answer": a.get("answer", "") or "",
                "url_supporting": a.get("url_supporting") if isinstance(a.get("url_supporting"), list) else [],
            }
    if "search" in out and out["search"] is not None and isinstance(out["search"], dict):
        pass  # will strip keys below
    if "knowledge_summary" in out and isinstance(out["knowledge_summary"], list):
        normalized = []
        for k in out["knowledge_summary"]:
            if isinstance(k, dict):
                claim = k.get("claim", str(k.get("url_supporting", "")))
                url = k.get("url_supporting", "")
                if isinstance(url, list):
                    url = url[0] if url else ""
                normalized.append({"claim": str(claim), "url_supporting": str(url)})
            else:
                normalized.append({"claim": str(k), "url_supporting": ""})
        out["knowledge_summary"] = normalized
    # Recursively remove any key not in whitelist (e.g. "sellToken", '"sellToken"') at any level
    return _strip_unknown_keys_recursive(out, _RESPONDER_TOP_KEYS)


class GeminiChatAdapter:
    """LangChain-style adapter for Gemini. Use get_llm('gemini-2.0-flash') and pass to preprocessor/responder."""

    def __init__(self, model: str = "gemini-2.0-flash", **kwargs):
        self._model_name = model
        self._kwargs = kwargs

    def with_structured_output(self, schema_class: Type[T]) -> _StructuredGemini:
        return _StructuredGemini(self._model_name, schema_class, **self._kwargs)


def _embedding_to_list(e) -> List[float]:
    """Normalize one embedding from API to list[float]."""
    if hasattr(e, "values"):
        return list(e.values)
    return list(e) if e is not None else []


class GeminiEmbeddings:
    """LangChain-compatible embeddings using Gemini (same GOOGLE_API_KEY as chat)."""

    def __init__(self, model: str = "models/gemini-embedding-001", **kwargs):
        _ensure_configured()
        self._model = model if model.startswith("models/") else f"models/{model}"
        self._kwargs = kwargs

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        result = genai.embed_content(model=self._model, content=texts, **self._kwargs)
        if hasattr(result, "embedding") and result.embedding is not None:
            return [_embedding_to_list(result.embedding)]
        if hasattr(result, "embeddings") and result.embeddings:
            return [_embedding_to_list(e) for e in result.embeddings]
        if isinstance(result, dict):
            emb = result.get("embedding") or result.get("embeddings", [])
            return [_embedding_to_list(e) for e in (emb if isinstance(emb, list) else [emb])]
        return []

    def embed_query(self, text: str) -> List[float]:
        out = self.embed_documents([text])
        return out[0] if out else []

    def __call__(self, text: str) -> List[float]:
        """Allow callable use: embeddings(text) for LangChain compatibility."""
        return self.embed_query(text)
