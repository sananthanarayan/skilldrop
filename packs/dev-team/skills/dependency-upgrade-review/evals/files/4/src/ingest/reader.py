"""Readers for the ingest pipeline.

Current-format files go through ``read_stream``. Archived ``.qsf1`` files
written before the 2024 migration are still replayed by the monthly backfill
job through ``read_legacy_archive``.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterator

import quillstream

from .client import fetch_with_retry


def read_stream(url: str) -> Iterator[bytes]:
    client = quillstream.Client(timeout=10)
    payload = fetch_with_retry(client, url)
    yield from payload.chunks()


def read_legacy_archive(path: Path) -> Iterator[bytes]:
    # Imported lazily: only the backfill job needs the old frame format.
    from quillstream.legacy import parse_frame

    data = path.read_bytes()
    offset = 0
    while offset < len(data):
        header, payload = parse_frame(data[offset:])
        yield payload
        offset += header.length
