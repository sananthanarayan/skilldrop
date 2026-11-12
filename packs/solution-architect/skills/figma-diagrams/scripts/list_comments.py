#!/usr/bin/env python3
"""List comments on a Figma file.

Usage:
    python list_comments.py <FILE_KEY_OR_URL>
"""

from __future__ import annotations

import sys

from _figma_client import extract_file_key, get


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        sys.stderr.write("usage: list_comments.py <FILE_KEY_OR_URL>\n")
        return 2
    file_key = extract_file_key(argv[0])
    data = get(f"/v1/files/{file_key}/comments")
    comments = data.get("comments", [])
    if not comments:
        print("(no comments)")
        return 0
    for c in comments:
        author = c.get("user", {}).get("handle", "<unknown>")
        ts = c.get("created_at", "")
        msg = c.get("message", "").strip().replace("\n", " ")
        resolved = " [resolved]" if c.get("resolved_at") else ""
        print(f"- {ts}  @{author}{resolved}: {msg}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
