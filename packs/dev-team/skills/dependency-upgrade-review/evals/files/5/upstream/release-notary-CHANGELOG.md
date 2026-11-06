# release-notary changelog

## 1.9.0 — 2026-10-02

- **Removed** the `legacyMode` option of `createNotary()`, deprecated since 1.6.0. Passing it now throws `TypeError: Unknown option "legacyMode"`. Manifests are always written in the v2 layout (`manifest.files[]` replaces the top-level `artifacts` map).
- Added opt-out usage reporting through the new `notary-telemetry` dependency. It runs at install time to detect the CI provider and sends an anonymous ping when `publish()` runs. Disable with `NOTARY_TELEMETRY=0`.
- Requires Node.js 20 or newer.
- Dropped `ansi-tint`; output colouring uses `util.styleText`.

## 1.8.3 — 2026-08-20

- Fixed: `publish({ sign: true })` silently skipped signing when `signingKey` was an empty string. It now throws `Error: signingKey is empty`.

## 1.8.2 — 2026-07-01

- Fixed Windows path separators in manifest entries.
