# Changelog

All notable changes to quillstream are documented here. This project follows Semantic Versioning.

## 3.1.0 — 2026-10-11

### Added
- Frame decoding is now delegated to the new `grainwire` package (`grainwire>=1.0,<2`), which is a required dependency. `grainwire` ships compiled wheels for CPython 3.10–3.13 on manylinux and macOS; other platforms build from sdist and need a Rust toolchain.
- `Client(..., compression="auto")` negotiates zstd when the server supports it.

### Fixed
- `Client.close()` no longer leaks a socket when called twice.

## 3.0.0 — 2026-08-29

### Breaking
- **Python 3.10 or newer is required.** Support for Python 3.8 and 3.9 has been dropped (`python_requires=">=3.10"`).
- **Removed the `quillstream.legacy` module**, deprecated since 2.2. `quillstream.legacy.parse_frame(buf)` is gone; use `quillstream.frames.decode(buf, strict=False)` instead. Note that `decode` returns a `Frame` object rather than a `(header, payload)` tuple; use `frame.header` and `frame.payload`.
- `Client.fetch()` now raises `quillstream.errors.QuillTimeout` when the request times out. Previously it returned `None`.
- Dropped the dependency on `compat-six`.

### Changed
- Minimum `typing-shimx` is now 4.8.

## 2.5.0 — 2026-06-02

### Deprecated
- Importing `quillstream.legacy` now emits a `DeprecationWarning` with the removal version (3.0).
- `Client.fetch()` returning `None` on timeout is deprecated; opt in to the 3.0 behaviour with `Client(raise_on_timeout=True)`.

### Added
- `quillstream.frames.decode()`.

## 2.4.1 — 2026-03-17

### Fixed
- Off-by-one in chunked frame reassembly for payloads larger than 64 KiB.
