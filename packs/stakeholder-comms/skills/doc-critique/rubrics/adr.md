# Rubric: ADR

Mirrors `adr-generator`'s quality bar.

## Blockers
- **Title is a noun phrase**, not a verb phrase or a question.
  ❌ *"Decide what database to use"* / *"Database decision"* ✅ *"Use Postgres as the primary OLTP datastore"*
- **At least 2 considered options.** If only one option appears, it's not a decision; it's a plan. Demand alternatives or downgrade the artifact to a design note.
- **Status is one of:** `Proposed | Accepted | Deprecated | Superseded by ADR-NNNN`. Anything else (e.g. `Final`, `Done`, `WIP`) breaks search/automation.
- **Decision is stated explicitly.** A reader must be able to extract the decision in one sentence without parsing the trade-offs first.
- **Consequences include trade-offs, not just upsides.** A consequences section with no ❌/⚠️ items hasn't engaged with the decision honestly.

## Major
- **Status of "Accepted" requires deciders listed.** Otherwise the audit trail is broken.
- **Every considered option has a why-not.** "We didn't pick DynamoDB" is not enough — it must say *why*.
- **Decision drivers tie to the chosen option's rationale.** If the drivers list QPS and cost, but the chosen option's rationale is "team familiarity", drivers are decorative.
- **Numbered correctly.** Sequential, zero-padded (`0007-`, not `7-` or `007-`).
- **MADR vs Nygard fit.** Heavy decisions in Nygard's 4-section format lose nuance; trivial decisions in MADR look bureaucratic. Note when the format doesn't fit the decision's weight.

## Minor
- **Date present and absolute** (`YYYY-MM-DD`, not "Q3 2024").
- **Filename matches slug:** `NNNN-kebab-case-title.md`.
- **Tags / context links** present if other ADRs supersede or relate to this one.
- **Active voice in the decision sentence.**
- **No "TBD"** in published ADRs — move to a follow-up.

## Nits
- Markdown formatting (headings, code-fence languages).
- Inconsistent verb tense (past vs present) — pick one.
- Bullet style consistency.

## What's working — look for
- Decision drivers tied directly to options' pros/cons.
- Honest "we picked the worse-on-paper option because X" — these are gold.
- Cross-links to the related design doc / spike / experiment.
- Real downsides in consequences, not throat-clearing.
