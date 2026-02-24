#!/usr/bin/env python3
"""
Fetch CoW Order Book OpenAPI spec from cowprotocol/services and save locally.

Usage (from repo root):
  python scripts/cow-2-fetch-openapi/main.py [--output data/cow-docs/openapi.yml]
"""
import argparse
import sys
from pathlib import Path

try:
    import urllib.request
except Exception:
    pass

OPENAPI_URL = "https://raw.githubusercontent.com/cowprotocol/services/main/crates/orderbook/openapi.yml"


def main():
    parser = argparse.ArgumentParser(description="Fetch Order Book OpenAPI spec")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/cow-docs/openapi.yml"),
        help="Output file path",
    )
    args = parser.parse_args()
    out = args.output.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    try:
        with urllib.request.urlopen(OPENAPI_URL, timeout=30) as resp:
            data = resp.read()
    except Exception as e:
        print(f"Failed to fetch {OPENAPI_URL}: {e}", file=sys.stderr)
        return 1

    out.write_bytes(data)
    print(f"Saved to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
