# Contributing

## Tooling

We use uv for environments. `uv sync` installs everything, including the dev group.

We moved from black to ruff in 2025: format with `uv run ruff format .` and lint with
`uv run ruff check .`. Please don't reintroduce black.

## Tests

Run `uv run pytest -m "not hardware"`.

Tests marked `hardware` talk to a live telemetry gateway on the plant network. They hang for
several minutes and then fail anywhere else, so only run them from the test bench at the
Eastmoor station.

## Deploying

Deploys are done by the on-call engineer with `scripts/deploy.sh`. Don't run it from a branch.
