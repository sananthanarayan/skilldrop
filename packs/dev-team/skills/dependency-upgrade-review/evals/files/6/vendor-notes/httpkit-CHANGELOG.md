# Changelog — github.com/fernwire/httpkit

Excerpt copied from the upstream repository's CHANGELOG.md at tag v1.8.4.

## v1.8.4 — 2026-10-02

### Added
- `WithTracer(t otelshim.Tracer)` option for OpenTelemetry spans. Pulls in
  `github.com/fernwire/otelshim` as a dependency. No behaviour change unless
  the option is passed. (#238)

### Fixed
- Data race in connection-pool metrics when `Stats()` is called concurrently
  with in-flight requests. (#240)

## v1.8.3 — 2026-09-18

### Changed
- `NewClient` no longer applies a default 30-second `Timeout`. The zero value
  now means **no client-level timeout**, matching `net/http.Client`. Callers
  that relied on the old default should pass `WithTimeout(30 * time.Second)`
  explicitly. Deadlines carried by the request `context.Context` are still
  honoured. (#231)

  We are shipping this in a patch release because the old default silently
  cut off long-polling and streaming callers, which we consider a bug.

### Fixed
- `Response.Body` is now always closed when `Do` returns an error after
  reading headers. (#229)

## v1.8.2 — 2026-08-30

### Changed
- Retry backoff is now computed by `github.com/fernwire/backoff` v0.4.0
  (previously v0.3.0). Jitter is full-jitter instead of equal-jitter; the
  maximum delay per attempt is unchanged at 2s. `WithRetries(n)` semantics
  are unchanged. (#224)

## v1.8.1 — 2026-08-04

### Fixed
- `WithBaseURL` now tolerates a trailing slash. (#219)
