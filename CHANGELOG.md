# Changelog

What shipped in each released version of `skilldrop-cli`. The site reads the newest three
entries into its **Recently shipped** section (RFC-0026), and `build_site.py` refuses to
build if the version at the top of this file disagrees with `package.json` — so a release
cannot ship undocumented.

Format: `## <version> — <YYYY-MM-DD>`, newest first, one bullet per user-visible change.
Bullets say what a user can now do, not which files moved.

## 0.11.4 — 2026-09-18

- New skill `output-hygiene`: finds what a machine left in agent-written text — invisible Unicode, non-breaking spaces, homoglyphs, harness-added provenance trailers, trailing chat closers — and separates what is safe to strip from what needs a decision (RFC-0025).
- The catalogue page now opens with its search box and filters visible instead of hiding all 57 skills behind a disclosure toggle (RFC-0026).
- Filter state lives in the URL, so a filtered view — one pack, one tier, one outcome — is a link you can send someone.
- New browse axis: seven **outcomes** answer "why am I here", alongside the six role packs that answer "who am I".
- The site shows its own version and its three most recent releases, so a visitor can tell the project is alive.

## 0.11.3 — 2026-08-10

- `validate.py` fails when a shipped skill has no README row, so the catalogue can no longer document less than it ships.
- Every RFC carries an accurate status, and the pre-commit checklist says which rules are machine-enforced and which are human judgment.

## 0.9.3 — 2026-08-07

- New skill `agent-adoption-stage`: places a team on an agent-adoption curve and names the next move (RFC-0024).

## 0.9.2 — 2026-08-07

- Four AI-adoption skills: `ai-readiness-assessment`, `ai-use-case-triage`, `ai-adoption-rollout`, `ai-usage-policy` (RFC-0023).

## 0.9.1 — 2026-08-06

- `skilldrop` read commands take `--json` (RFC-0021), so the catalogue is scriptable.
- Supply-chain scanning on the code that runs on other people's machines (RFC-0022).
- Evals backfilled across the activation-collision clusters that actually compete.

## 0.9.0 — 2026-08-05

- `skilldrop install --panel review` installs the whole reviewer panel in one command (RFC-0020).
- Model map refreshed to the Claude 5 family; conformance to the Agent Skills open standard declared.
