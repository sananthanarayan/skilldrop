# Governance, risk and compliance

Governance, risk and compliance drafts for compliance leads, DPOs and risk owners: a risk register with a checked heat map, a GDPR data protection impact assessment, a SOC 2 control-to-evidence map, and answers to a customer security questionnaire drawn from your own evidence, each prepared for a qualified person to review.

`/plugin install grc@skilldrop` · generated from [`main`](https://github.com/sananthanarayan/skilldrop) — do not edit.

## Start here: Turn a list of worries into a scored, owned risk register

Paste this into Claude Code:

```text
Build a risk register for our office relocation project. Risks: the lease on the new floor isn't signed yet (owner: Facilities Manager, Dana Cole), the network fit-out might slip past the move date (owner: IT Manager, Raj Patel), and staff may push back on desk sharing (owner: HR Business Partner, Lena Fox). Use a 5x5 scale; today is 2026-10-01.
```

- **Before you start:** A list of the risks you already worry about, with an owner for each if you know them
- **How to tell it worked:** risk-register writes a CSV where each risk has a cause, an event and a consequence, inherent and residual scores on a defined 5x5 scale, a named owner and a treatment with a date; its check script prints PASS, a heat map, and the top risks needing a decision.
- **If nothing happens:** If the script fails, read its error lines: each names the row and the field to fix. If risk-register does not activate, ask for it by name ("use risk-register").

## Loops

- `ship-a-draft`

## Skills

- `brief-intake`
- `council-review`
- `doc-critique`
- `dpia`
- `output-hygiene`
- `risk-register`
- `security-questionnaire-response`
- `soc2-evidence-map`

More: https://sananthanarayan.github.io/skilldrop/packs/grc/
