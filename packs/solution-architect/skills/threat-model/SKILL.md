---
name: threat-model
description: Produce a STRIDE threat model from a design doc, architecture description, or feature spec — assets and trust boundaries first, threats anchored to boundary crossings with concrete attack scenarios, severity-ranked with verifiable mitigations. Use when the user asks to threat-model a design, run a security review of an architecture, ask "how could this be attacked", or needs security sign-off input before build.
---

# threat-model

Finds the attacks a design permits *before* the code exists, when fixes are a diagram edit instead of a migration. Design-phase counterpart to `devils-advocate` (which attacks written code); consumes `design-doc` or `reverse-architecture` output directly. Threats live where data crosses a trust boundary — the model is anchored there, not in a generic checklist.

## How to respond

1. **Establish the system before any threats.** From the input, extract and state:
   - **Assets** — what an attacker wants (credentials, PII, payment data, compute, availability), ranked by damage-if-lost
   - **Entry points** — every way data or commands get in (APIs, queues, file uploads, admin panels, CI/CD, third-party webhooks)
   - **Trust boundaries** — every line where the trust level changes (internet→edge, service→service, app→DB, human→system, tenant→tenant)
   Ask at most 2 questions, and spend them on trust boundaries — misplaced boundaries invalidate the whole model. Tag everything else `[assumption]`.

2. **Enumerate boundary crossings, then run STRIDE per crossing** using the question banks in [`reference.md`](reference.md) — Spoofing, Tampering, Repudiation, Information disclosure, Denial of service, Elevation of privilege. Not every category applies at every crossing; say "n/a" with one word of why rather than padding.

3. **Write each threat as a concrete attack scenario**: actor → path → result. ✅ *"A tenant crafts a report name containing `../`, the export service writes to another tenant's S3 prefix, cross-tenant data exposure"* — ❌ *"Path traversal is possible"*. A threat that can't be narrated as a scenario isn't understood yet.

4. **Severity-rank with the shared markers** — 🟥 critical (unauthenticated or cross-tenant compromise of a top asset), 🟧 high (authenticated bypass, single-tenant data exposure), 🟨 medium (requires chaining or insider position), ⚪ low/accepted. Likelihood × impact, judged against *this* system's assets — not CVSS theater. If everything is 🟥, the ranking failed.

5. **Assess existing mitigations honestly** before recommending new ones. Each threat gets: what already mitigates it (and whether that's verified or assumed), then the recommended mitigation with a **verification step** — ✅ *"Presigned URLs scoped to tenant prefix; verify with a cross-tenant fetch test in CI"* — ❌ *"Use proper access controls"*.

6. **Force the insider and authz passes.** Two systematic blind spots, swept explicitly: what can a *legitimate authenticated user* do to another tenant or to escalate (authn is not authz), and what can a malicious or compromised insider/CI-token do. One finding or an explicit all-clear for each.

7. **Emit the model in one message**: system summary (assets / entry points / boundaries), findings grouped by severity, the n/a ledger, **assumptions**, **out of scope**, and **questions for the team** — the unknowns that block a finding from being confirmed or dismissed. End with the revisit trigger: the model is stale when a new entry point, boundary, or asset class appears.

## Useful references in this skill

- [`reference.md`](reference.md) — STRIDE question banks per boundary type + common-mitigation table
- [`examples/document-upload.md`](examples/document-upload.md) — worked example: upload feature → 6 ranked findings

## Quality bar

- **Every threat is anchored** to a named trust-boundary crossing or asset. An unanchored finding is checklist residue — cut it.
- **Every threat narrates a scenario** with actor, path, and result. "X is possible" is not a finding.
- **Severity spread is honest.** A model where everything is critical (or nothing is) hasn't ranked anything; the 🟥 set is what you'd halt the build for.
- **Every recommended mitigation has a verification step** a reviewer can run or check. Advice without verification is a wish.
- **Existing mitigations are credited** — and marked verified vs assumed. A model that ignores what the design already does right teaches the team to ignore the model.
- **The insider and authz sweeps produced output** — findings or an explicit reasoned all-clear, never silence.

## When to use this skill

- ✅ A design doc or RFC needs security scrutiny before implementation starts
- ✅ "How could this be attacked?" for a new feature, integration, or entry point
- ✅ Input for a formal security review / sign-off gate
- ✅ A `reverse-architecture` extraction of a legacy system that never had a threat model

## When NOT to use this skill

- ❌ Reviewing written code for vulnerabilities — that's `devils-advocate` (its security lens) or `sonar-review`
- ❌ Compliance attestation (SOC2, PCI evidence) — this models attacks, it doesn't certify controls
- ❌ Incident analysis after an exploit — that's `postmortem-generator`
- ❌ Pen-testing a live system — this is paper analysis; it tells the pen test where to aim

## Anti-patterns to avoid

- ❌ **OWASP-checklist dumping** — twenty generic items ("ensure input validation") untied to any boundary in *this* system. Volume isn't rigor.
- ❌ **Stopping at authentication.** "Users must log in" answers spoofing only; the authz pass (tenant→tenant, user→admin) is where real findings live.
- ❌ **"Use encryption" as a mitigation.** Of what, where, against which threat? Encryption at rest does nothing for a tampered request in flight.
- ❌ **Modeling only the happy architecture.** Admin panels, CI/CD pipelines, support tooling, and webhook receivers are entry points — usually the softest ones.
- ❌ **Inflating severity to be taken seriously.** One cried-wolf 🟥 and the next model gets skimmed.
- ❌ **One-and-done modeling.** A threat model without a revisit trigger expires silently the first time the design changes.
