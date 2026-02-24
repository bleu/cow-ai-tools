"""
Tests for Gemini adapter: ensure payloads with keys like \"sellToken\" never reach Pydantic.

The KeyError: '\"sellToken\"' occurs when Gemini returns JSON with that key and Pydantic
tries to look up __fields__['\"sellToken\"']. These tests verify our sanitization and
_build_responder_payload prevent that.
"""
import pytest

from op_brains.chat.gemini_adapter import (
    _build_responder_payload,
    _remove_blacklisted_keys_recursive,
    _is_blacklisted_key,
)


def _payload_has_selltoken_key(obj, path=""):
    """Return True if any key in obj (recursively) looks like sellToken/buyToken."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if _is_blacklisted_key(k):
                return True
            if _payload_has_selltoken_key(v, path + "." + str(k)):
                return True
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            if _payload_has_selltoken_key(item, path + "[%s]" % i):
                return True
    return False


class TestBuildResponderPayload:
    """_build_responder_payload must never pass through keys like \"sellToken\"."""

    def test_strips_selltoken_from_answer(self):
        raw = {
            "knowledge_summary": [{"claim": "c1", "url_supporting": "https://a"}],
            "answer": {"answer": "text", "url_supporting": [], '"sellToken"': "0x123"},
            "search": {"questions": [], "keywords": [], "type_search": "factual", "user_knowledge": ""},
        }
        out = _build_responder_payload(raw)
        assert not _payload_has_selltoken_key(out)
        assert out["answer"]["answer"] == "text"
        assert "url_supporting" in out["answer"]
        assert '"sellToken"' not in out.get("answer", {})

    def test_strips_selltoken_from_search(self):
        raw = {
            "knowledge_summary": [],
            "search": {
                "questions": ["q1"],
                "keywords": ["k1"],
                "type_search": "factual",
                "user_knowledge": "",
                '"sellToken"': "0x456",
                "sellAmount": "1000",
            },
        }
        out = _build_responder_payload(raw)
        assert not _payload_has_selltoken_key(out)
        assert out["search"]["questions"] == ["q1"]
        assert '"sellToken"' not in out.get("search", {})
        assert "sellAmount" not in out.get("search", {})

    def test_strips_selltoken_from_knowledge_summary_items(self):
        raw = {
            "knowledge_summary": [
                {"claim": "claim1", "url_supporting": "https://x", "sellToken": "0x"},
            ],
            "answer": None,
        }
        out = _build_responder_payload(raw)
        assert not _payload_has_selltoken_key(out)
        assert len(out["knowledge_summary"]) == 1
        assert out["knowledge_summary"][0]["claim"] == "claim1"
        assert "sellToken" not in out["knowledge_summary"][0]

    def test_answer_string_normalized(self):
        raw = {"knowledge_summary": [], "answer": "Just a string answer."}
        out = _build_responder_payload(raw)
        assert out["answer"] == {"answer": "Just a string answer.", "url_supporting": []}

    def test_missing_knowledge_summary_defaults_to_empty_list(self):
        raw = {"answer": None}
        out = _build_responder_payload(raw)
        assert out["knowledge_summary"] == []


class TestBlacklistKeys:
    """_is_blacklisted_key and _remove_blacklisted_keys_recursive."""

    @pytest.mark.parametrize("key", ['"sellToken"', '"buyToken"', "sellToken", "buyToken"])
    def test_blacklisted_keys(self, key):
        assert _is_blacklisted_key(key) is True

    def test_allowed_keys(self):
        assert _is_blacklisted_key("answer") is False
        assert _is_blacklisted_key("url_supporting") is False
        assert _is_blacklisted_key("knowledge_summary") is False
        assert _is_blacklisted_key("questions") is False

    def test_remove_blacklisted_recursive(self):
        obj = {"answer": {"answer": "x", "url_supporting": [], '"sellToken"': "0x"}}
        out = _remove_blacklisted_keys_recursive(obj)
        assert not _payload_has_selltoken_key(out)


class TestResponderPayloadAcceptedByPydantic:
    """Payload from _build_responder_payload must be accepted by a Responder-like schema."""

    def test_minimal_payload_has_required_keys(self):
        raw = {"knowledge_summary": [], "answer": None}
        out = _build_responder_payload(raw)
        assert "knowledge_summary" in out
        assert isinstance(out["knowledge_summary"], list)
        # answer can be absent when not in raw; search can be absent
        assert not _payload_has_selltoken_key(out)
