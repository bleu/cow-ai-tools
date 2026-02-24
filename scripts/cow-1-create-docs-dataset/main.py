#!/usr/bin/env python3
"""
Build the CoW docs artifact for RAG ingestion.

Clones cowprotocol/docs, walks docs/cow-protocol (and docs/README.md),
outputs a single file in the format expected by CowDocsProcessingStrategy:

  ==> docs/relative/path.md <==
  content here...

Run from repo root:
  python scripts/cow-1-create-docs-dataset/main.py [--output data/cow-docs/cow_docs.txt]
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

COW_DOCS_REPO = "https://github.com/cowprotocol/docs.git"
DEFAULT_BRANCH = "main"

# In scope for integration docs (RFP): cow-protocol only. Out: cow-amm, mevblocker.
INCLUDE_PREFIXES = ("docs/cow-protocol/", "docs/README.md")
INCLUDE_EXACT = ("docs/README.md",)


def clone_or_pull(repo_dir: Path, skip_pull: bool = False) -> None:
    if repo_dir.exists():
        if skip_pull:
            return
        r = subprocess.run(
            ["git", "pull", "--depth", "1"],
            cwd=repo_dir,
            capture_output=True,
        )
        if r.returncode != 0:
            print("Warning: git pull failed, using existing repo.", file=sys.stderr)
    else:
        repo_dir.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["git", "clone", "--depth", "1", "--branch", DEFAULT_BRANCH, COW_DOCS_REPO, str(repo_dir)],
            check=True,
            capture_output=True,
        )


def should_include(rel_path: str) -> bool:
    if rel_path in INCLUDE_EXACT:
        return True
    return rel_path.startswith(INCLUDE_PREFIXES[0])


def build_artifact(repo_dir: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    docs_dir = repo_dir / "docs"
    if not docs_dir.exists():
        raise SystemExit("docs/ not found in cloned repo")

    out_lines: list[str] = []
    for root, _dirs, files in os.walk(docs_dir):
        root_path = Path(root)
        for name in sorted(files):
            if not name.endswith(".md"):
                continue
            full = root_path / name
            try:
                rel = full.relative_to(repo_dir).as_posix()
            except ValueError:
                continue
            if not should_include(rel):
                continue
            raw = full.read_text(encoding="utf-8", errors="replace")
            # Normalize line endings and ensure trailing newline
            content = raw.replace("\r\n", "\n").replace("\r", "\n")
            if content and not content.endswith("\n"):
                content += "\n"
            out_lines.append(f"==> {rel} <==\n")
            out_lines.append(content)

    output_path.write_text("".join(out_lines), encoding="utf-8")
    print(f"Wrote {len([l for l in out_lines if l.startswith('==>')])} files to {output_path}", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build CoW docs artifact for RAG")
    parser.add_argument(
        "--repo-dir",
        type=Path,
        default=Path("data/cow-docs/repo"),
        help="Directory to clone cowprotocol/docs into",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/cow-docs/cow_docs.txt"),
        help="Output artifact path (==> path <== format)",
    )
    parser.add_argument(
        "--no-pull",
        action="store_true",
        help="Skip git pull when repo already exists",
    )
    args = parser.parse_args()
    repo_dir = args.repo_dir.resolve()
    output_path = args.output.resolve()

    clone_or_pull(repo_dir, skip_pull=args.no_pull)
    build_artifact(repo_dir, output_path)


if __name__ == "__main__":
    main()
