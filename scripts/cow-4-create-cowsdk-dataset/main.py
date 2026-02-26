#!/usr/bin/env python3
"""
Build the CoW SDK (cowprotocol/cow-sdk) artifact for RAG ingestion.

Clones cowprotocol/cow-sdk, collects README.md and docs/*.md,
outputs a single file in the same format as cow_docs (==> path <== content)
so CowSdkDocsProcessingStrategy can ingest it.

Run from repo root:
  python scripts/cow-4-create-cowsdk-dataset/main.py [--output data/cow-docs/cow_sdk_docs.txt]
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

COW_SDK_REPO = "https://github.com/cowprotocol/cow-sdk.git"
DEFAULT_BRANCH = "main"

# Root README, docs/, packages/*/README (sdk, trading, order-book, order-signing), examples
INCLUDE_FILES = {"README.md"}
INCLUDE_PREFIX = "docs/"
INCLUDE_PACKAGES_README = "packages/"
INCLUDE_EXAMPLES_README = "examples/"


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
            ["git", "clone", "--depth", "1", "--branch", DEFAULT_BRANCH, COW_SDK_REPO, str(repo_dir)],
            check=True,
            capture_output=True,
        )


def should_include(rel_path: str) -> bool:
    if rel_path == "README.md":
        return True
    if rel_path.startswith(INCLUDE_PREFIX) and rel_path.endswith(".md"):
        return True
    # packages/<name>/README.md or packages/<name>/CHANGELOG.md (skip CHANGELOG for brevity)
    if rel_path.startswith(INCLUDE_PACKAGES_README) and rel_path.endswith("README.md"):
        return True
    # examples/<stack>/<adapter>/README.md
    if rel_path.startswith(INCLUDE_EXAMPLES_README) and rel_path.endswith("README.md"):
        return True
    return False


def build_artifact(repo_dir: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    out_lines: list[str] = []
    for root, _dirs, files in os.walk(repo_dir):
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
            content = raw.replace("\r\n", "\n").replace("\r", "\n")
            if content and not content.endswith("\n"):
                content += "\n"
            out_lines.append(f"==> {rel} <==\n")
            out_lines.append(content)

    output_path.write_text("".join(out_lines), encoding="utf-8")
    count = len([l for l in out_lines if l.startswith("==>")])
    print(f"Wrote {count} files to {output_path}", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build CoW SDK (cow-sdk repo) artifact for RAG")
    parser.add_argument(
        "--repo-dir",
        type=Path,
        default=Path("data/cow-docs/cow-sdk-repo"),
        help="Directory to clone cowprotocol/cow-sdk into",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/cow-docs/cow_sdk_docs.txt"),
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
