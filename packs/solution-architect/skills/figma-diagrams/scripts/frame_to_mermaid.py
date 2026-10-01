#!/usr/bin/env python3
"""Best-effort: turn a Figma frame's child structure into a first-pass Mermaid flowchart.

This won't perfectly capture visual layout — it walks the node tree, looks at
text labels and parent/child relationships, and produces a Mermaid `flowchart TB`
you can hand-edit. Useful as a starting point when reverse-engineering a
diagram a colleague drew in Figma.

Usage:
    python frame_to_mermaid.py <FILE_KEY_OR_URL> <NODE_ID>
"""

from __future__ import annotations

import re
import sys

from _figma_client import extract_file_key, get

SAFE_ID_RE = re.compile(r"[^A-Za-z0-9_]+")


def safe_id(node_id: str) -> str:
    return "n" + SAFE_ID_RE.sub("_", node_id)


def best_label(node: dict) -> str:
    """Pick a human label for a node — its name, or a TEXT descendant if name is generic."""
    name = (node.get("name") or "").strip()
    if name and not name.lower().startswith(("frame", "group", "rectangle", "ellipse")):
        return name
    for child in node.get("children", []) or []:
        if child.get("type") == "TEXT":
            chars = (child.get("characters") or "").strip()
            if chars:
                return chars
        deeper = best_label(child)
        if deeper and deeper != child.get("name"):
            return deeper
    return name or node.get("type", "node")


def emit(node: dict, parent_id: str | None, lines: list[str], edges: list[str]) -> None:
    type_ = node.get("type")
    if type_ in {"DOCUMENT", "CANVAS"}:
        for c in node.get("children", []) or []:
            emit(c, parent_id, lines, edges)
        return

    my_id = safe_id(node["id"])
    label = best_label(node).replace('"', "'")[:60]

    if type_ in {"FRAME", "GROUP", "SECTION"}:
        lines.append(f'    subgraph {my_id}["{label}"]')
        for c in node.get("children", []) or []:
            emit(c, my_id, lines, edges)
        lines.append("    end")
    elif type_ in {"RECTANGLE", "ELLIPSE", "COMPONENT", "INSTANCE", "TEXT"}:
        if type_ == "ELLIPSE":
            lines.append(f'    {my_id}(("{label}"))')
        else:
            lines.append(f'    {my_id}["{label}"]')
        if parent_id:
            edges.append(f"    {parent_id} --- {my_id}")
    elif type_ == "CONNECTOR":
        ep = node.get("connectorStart", {})
        eq = node.get("connectorEnd", {})
        a = ep.get("endpointNodeId")
        b = eq.get("endpointNodeId")
        if a and b:
            edges.append(f"    {safe_id(a)} --> {safe_id(b)}")
    else:
        for c in node.get("children", []) or []:
            emit(c, parent_id, lines, edges)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        sys.stderr.write("usage: frame_to_mermaid.py <FILE_KEY_OR_URL> <NODE_ID>\n")
        return 2
    file_key = extract_file_key(argv[0])
    node_id = argv[1]

    data = get(f"/v1/files/{file_key}/nodes", params={"ids": node_id})
    node = data.get("nodes", {}).get(node_id, {}).get("document")
    if not node:
        sys.stderr.write(f"error: node {node_id} not found in {file_key}\n")
        return 1

    lines: list[str] = ["flowchart TB"]
    edges: list[str] = []
    emit(node, None, lines, edges)
    lines.extend(edges)

    print("```mermaid")
    print("\n".join(lines))
    print("```")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
