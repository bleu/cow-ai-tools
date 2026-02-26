"""Shared chat utils (e.g. normalize_answer_text)."""
import re

_CODE_BLOCK_RE = re.compile(r"```[\s\S]*?```")


def normalize_answer_text(text: str) -> str:
    """Collapse line breaks outside code blocks into spaces for cleaner display."""
    if not text or "\n" not in text:
        return text
    text = re.sub(r"[ \t]{2,}\r?\n", " ", text)

    def process_part(part: str) -> str:
        part = part.replace("\r\n", "\n").replace("\r", "\n")
        one_line = " ".join(part.splitlines())
        return re.sub(r"[ \t]+", " ", one_line).strip()

    parts = []
    last = 0
    for m in _CODE_BLOCK_RE.finditer(text):
        parts.append(process_part(text[last : m.start()]))
        parts.append(m.group(0))
        last = m.end()
    parts.append(process_part(text[last:]))
    return "".join(parts)
