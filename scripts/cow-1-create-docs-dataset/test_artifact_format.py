#!/usr/bin/env python3
"""
Test artifact format and CowDocsProcessingStrategy parsing logic without full rag_brains/cow_brains deps.
Run from repo root: python scripts/cow-1-create-docs-dataset/test_artifact_format.py
"""
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT = REPO_ROOT / "data" / "cow-docs" / "cow_docs.txt"


def path_to_url(rel_path: str) -> str:
    base = "https://docs.cow.fi/"
    s = rel_path.strip()
    if s.endswith(".md"):
        s = s[:-3]
    if s == "docs/README":
        return base.rstrip("/")
    if s.startswith("docs/"):
        s = s[5:]  # len("docs/") == 5
    return (base + s).rstrip("/")


def parse_artifact(file_path: Path) -> list[tuple[str, str, str]]:
    """Returns list of (full_path, url, content_snippet)."""
    text = file_path.read_text(encoding="utf-8", errors="replace")
    parts = re.split(r"==> | <==", text)
    docs = []
    path_parts = []
    for d in parts:
        stripped = d.strip()
        if stripped and "\n" not in d:
            path_parts = [p.strip() for p in d.split("/") if p.strip()]
        elif path_parts and stripped:
            path_str = "/".join(path_parts[:-1])
            doc_name = path_parts[-1]
            full_path = f"{path_str}/{doc_name}" if path_str else doc_name
            url = path_to_url(full_path)
            docs.append((full_path, url, d[:200].replace("\n", " ")))
    return docs


def main():
    if not ARTIFACT.exists():
        print(f"FAIL: Artifact not found at {ARTIFACT}")
        print("Run: python scripts/cow-1-create-docs-dataset/main.py --output data/cow-docs/cow_docs.txt")
        sys.exit(1)

    docs = parse_artifact(ARTIFACT)
    print(f"Parsed {len(docs)} documents from artifact")

    if len(docs) < 10:
        print("FAIL: Expected at least 10 documents")
        sys.exit(1)

    # Spot-check URLs (base is https://docs.cow.fi or https://docs.cow.fi/)
    sample = docs[0]
    assert sample[1].startswith("https://docs.cow.fi"), f"URL should start with docs.cow.fi: {sample[1]}"
    assert "docs/README" in sample[0] or "cow-protocol" in sample[0], f"Path should be docs/...: {sample[0]}"

    # Check we have cow-protocol content
    cow_protocol_docs = [d for d in docs if "cow-protocol" in d[0]]
    print(f"  - {len(cow_protocol_docs)} under docs/cow-protocol/")
    if not cow_protocol_docs:
        print("FAIL: No docs/cow-protocol/ paths found")
        sys.exit(1)

    print("OK: Artifact format and parsing logic validated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
