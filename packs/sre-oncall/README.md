# SRE / on-call

Operate the service: runbooks, observability design, incident communications, postmortems, and capacity/cost models.

`/plugin install sre-oncall@skilldrop` · generated from [`main`](https://github.com/sananthanarayan/skilldrop) — do not edit.

## Start here: Write the runbook an on-call engineer can follow at 3am

Paste this into Claude Code:

```text
Write a runbook for our payments-api service: it runs in the Kubernetes namespace payments, depends on Postgres and Stripe, and pages the payments on-call rotation.
```

- **How to tell it worked:** runbook-generator returns a runbook with rollback commands, the common incidents and what to do for each, and an escalation path. Facts you did not give it are marked missing, not invented.
- **If nothing happens:** If runbook-generator does not activate, ask for it by name ("use runbook-generator") and check that its folder exists in your skills folder (`~/.claude/skills/` by default).

## Loops

- `ship-a-draft`
- `operate`

## Skills

- `brief-intake`
- `capacity-cost-model`
- `cloud-cost-review`
- `council-review`
- `delivery-metrics-report`
- `doc-critique`
- `incident-comms`
- `observability-plan`
- `output-hygiene`
- `postmortem-generator`
- `runbook-generator`

More: https://sananthanarayan.github.io/skilldrop/packs/sre-oncall/
