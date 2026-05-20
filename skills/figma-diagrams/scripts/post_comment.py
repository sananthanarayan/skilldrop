#!/usr/bin/env python3
"""Post a comment on a Figma file.

Usage:
    python post_comment.py <FILE_KEY_OR_URL> "<message>" [--node-id NODE_ID]

If --node-id is given, the comment is pinned to the centroid of that node.
"""

from __future__ import annotations

import argparse
import sys

from _figma_client import extract_file_key, get, post


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("file", help="Figma file URL or bare file key")
    ap.add_argument("message", help="Comment text")
    ap.add_argument("--node-id", help="Node ID to pin the comment to (e.g. 1:23)")
    args = ap.parse_args(argv)

    file_key = extract_file_key(args.file)

    body: dict = {"message": args.message}

    if args.node_id:
        nodes = get(f"/v1/files/{file_key}/nodes", params={"ids": args.node_id})
        node = nodes.get("nodes", {}).get(args.node_id, {}).get("document", {})
        box = node.get("absoluteBoundingBox")
        if not box:
            sys.stderr.write(
                f"error: could not resolve node {args.node_id} in file {file_key}\n"
            )
            return 1
        body["client_meta"] = {
            "node_id": args.node_id,
            "node_offset": {
                "x": box["width"] / 2,
                "y": box["height"] / 2,
            },
        }

    resp = post(f"/v1/files/{file_key}/comments", body)
    print(f"posted: comment_id={resp.get('id')}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
