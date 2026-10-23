# Tour: {repo name}, for {the change, in one line}

_Read on {date}. Scope: {the path from the entry point to the change's far edge}. Skipped on purpose: {areas not on the path, e.g. "the admin UI, the billing service, deployment config"}._

{Any `[assumption]` lines go here, first, one per line.}

<!-- Citation key, for the writer (delete before sending):
     `path:line` = read there · [inferred] = not verified, reason given ·
     ran: passed / ran: failed (first error line) / read, not run · derived from <source> -->

## What matters for this change

<!-- 3–5 bullets. The things that change what the person does in the next hour: the README claim that's wrong, the second copy, the generated file, the test gap, the env var it won't start without. Each cites a file. -->

- {…} (`path:line`)

## Run it

<!-- ≤ ~15 lines. Commands only from CI / package scripts / Makefile / tox / nox / pyproject. CI's form wins. -->

| To | Command | Source | Status |
|---|---|---|---|
| Install | `{…}` | `{path:line}` | read, not run |
| Test (whole suite) | `{…}` | `{path:line}` | {ran: passed / ran: failed: … / read, not run} |
| Test (this area) | `{…}` | derived from `{path:line}` | {…} |
| Lint / typecheck | `{…}` | `{path:line}` | {…} |
| Run locally | `{…}` | `{path:line}` | {…} |

Needs: {env vars and services the commands need, each with where it is read or set, e.g. `DATABASE_URL` (`src/config.py:9`; CI sets it at `.github/workflows/ci.yml:14`)}.

## The path this change touches

<!-- ≤ 10 hops, entry point first, stop at the change's far edge. -->

1. `{path:line}` `{function}`: {what happens here}
2. …

## Where the change goes

<!-- Files and functions, each with the sibling pattern that justifies it. Then everything that must change with it. -->

- `{path}` `{function}`: {what to add} because {sibling pattern, cited}
- Must change with it: {spec + regenerate command / registry entry / second copy}, (`path:line`)

## Conventions the code follows

<!-- ≤ ~15 lines. Only the ones this change will hit. Each from code, cited. -->

- **Errors:** {…} (`path:line`)
- **Tests:** {location, naming, fixtures} (`path`)
- **Config:** {how it is read} (`path:line`)
- **Naming:** {…} (`path:line`)

## Traps

<!-- Every check reports. "none found" is an answer. -->

- **Generated:** {file} from {source}, regenerate with `{command}` (`path:line`); CI drift check: {yes, `path:line` / none}
- **Second copy:** {where the same logic lives} (`path:line`), or none found (searched for {identifiers})
- **Untested on the path:** {functions} or none
- **Tests the default command skips:** {marker / build tag / glob} (`path:line`) or none
- **Env vars and flags on the path:** `{NAME}` default {…} (`path:line`)
- **Vendored:** {…} or none

## Where the README is wrong

<!-- One line each, both citations. Omit the section only if every README claim checked out, and say "README checked: no conflicts." in the scope line instead. -->

- README says {…} (`README.md:{n}`); the code {…} (`path:line`). Follow the code.

## Tests for this area

- Covered by: `{test file}` ({what it asserts})
- Run just these: `{derived command}` (derived from `{path:line}`)
- Not covered: {functions with no test}, or "every function on the path has a test"

## First step

{Do X in `path`; run `command`; expect {result}.}

## Open questions for a maintainer

<!-- ≤ 5. Each answerable in a sentence, each pointing at the evidence that raised it. -->

1. {…} (`path:line`)
