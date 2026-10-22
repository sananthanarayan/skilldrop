# 3. A separate thumbnail service

Date: 2023-09-11

## Status

Accepted

## Context

Resizing product images inside the API blocks request threads.

## Decision

Image resizing runs in its own service, `services/thumbnailer/`, which consumes `resize` jobs
from the queue described in ADR-0002.

## Consequences

The API never touches image bytes after upload.
