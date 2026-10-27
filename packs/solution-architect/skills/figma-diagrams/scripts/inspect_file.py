#!/usr/bin/env python3
"""Print a tree summary of a Figma file: pages → frames → top-level groups.

Usage:
    python inspect_file.py <FILE_KEY_OR_URL> [--depth N]
"""

from __future__ import annotations

import argparse
import sys

from _figma_client import extract_file_key, get


def walk(node: dict, depth: int, max_depth: int) -> None:
    if depth > max_depth:
        return
    indent = "  " * depth
    name = node.get("name", "<unnamed>")
    type_ = node.get("type", "?")
    id_ = node.get("id", "?")
    print(f"{indent}- [{type_}] {name}  (id={id_})")
    for child in node.get("children", []) or []:
        walk(child, depth + 1, max_depth)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("file", help="Figma file URL or bare file key")
    ap.add_argument("--depth", type=int, default=3, help="Max tree depth to print")
    args = ap.parse_args(argv)

    file_key = extract_file_key(args.file)
    data = get(f"/v1/files/{file_key}")

    print(f"file: {data.get('name')!r}")
    print(f"last modified: {data.get('lastModified')}")
    print(f"version: {data.get('version')}")
    print()
    walk(data["document"], depth=0, max_depth=args.depth)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
