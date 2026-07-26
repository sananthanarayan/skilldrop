---
rfc: 0008
title: Agent threat model (lethal trifecta)
status: implemented
date: 2026-07-26
author: sananthanarayan
---

# RFC-0008: Agent threat model (lethal trifecta)

## Problem / use case

Someone is about to ship an agent — a Claude Code setup with MCP servers, a support bot with a retrieval index and a Slack webhook, a CI agent that reads PR comments and can push. The question they need answered before launch is not "what are this system's STRIDE categories" but "**can untrusted text reaching this agent cause it to move private data somewhere the attacker can read it?**"

Simon Willison's *lethal trifecta* names the structural condition: an agent holding (1) access to private data, (2) exposure to untrusted content, and (3) an exfiltration vector is compromised by construction, because an LLM cannot reliably separate instructions from data. Microsoft 365 Copilot and ChatGPT connectors both shipped zero-click exfiltration bugs on exactly this shape. The durable fix is architectural — remove one leg — and it has to be decided at design time, because after launch the tool permissions are load-bearing.

skilldrop has 48 skills and **zero coverage**: no skill mentions prompt injection, the trifecta, or exfiltration. `threat-model` (STRIDE) is aimed at systems and has no category where "the model obeys text it read" fits. The `Agent engineering` category can currently design a loop, decompose into subagents, and budget the spend — but has nothing that says the deployment is unsafe.

## Fit check

New skill. Four criteria:

- **Concrete artifact:** a markdown threat model — a capability inventory (every tool, MCP server, retrieval source, and egress path), the trifecta matrix scoring each leg, the named broken leg with the design change that breaks it, residual risks, and a pre-launch checklist.
- **Portable:** plain `SKILL.md` + `reference.md` + `templates/`, no scripts, no API. Copy-installs like every other skill.
- **Opinionated:** it refuses the two answers practitioners reach for first. *"We instruct the model to ignore injected instructions"* is not a control — it is the thing the attack defeats. *"We added an injection classifier"* is defense in depth, never the broken leg. Every trifecta-complete path must be resolved by an architectural change or explicitly accepted in writing by a named owner.
- **Category:** `Agent engineering` — completes design (`agent-loop-design`) / decompose (`subagent-design`) / budget (`agent-budget`) / **secure**.

## Proposal

- **Name:** `agent-threat-model`. Tier `heavy`, matching the other adversarial-judgment skills (`threat-model`, `devils-advocate`, `council-review`). Packs: `ai-engineering`, `dev-team`.
- **Intake:** an agent description, an MCP/tool config, a system prompt, an `agent-loop-design` output, or a repo. Degrades to `[assumption]` for unstated capabilities; emits `BLOCKED: need <X>` only when no tool or data inventory can be established at all — with nothing to inventory there is no model to build.
- **Method:**
  1. **Capability inventory** — enumerate tools/MCP servers, data reachable through each, and every egress path. Egress is the leg practitioners miss: image rendering, markdown links, error messages, and "read-only" web fetch are all exfiltration vectors.
  2. **Trifecta matrix** — per capability path, mark private-data / untrusted-content / egress. Any path holding all three is 🟥 and requires a broken leg.
  3. **Break a leg** — the recommended architectural change, chosen from a ranked menu (split the agent so no single one both reads untrusted content and holds privileged tools; drop the tool; allowlist egress; human approval on the acting step; sanitize at the trust boundary).
  4. **Residual risk + pre-launch checklist** — what remains, who accepted it, and what to verify before shipping.
- **`related`:** `threat-model` (system-level STRIDE, runs alongside), `agent-loop-design` (its human gates are one of the mitigations here), `subagent-design` (the split-agent mitigation is that skill's topology work), `agent-budget` (a runaway loop is a cost incident, not a security one — named to keep the boundary clear).
- **Quality bar (sketch):** every capability path scored on all three legs, no "the prompt tells it not to" as a mitigation, every 🟥 path either broken or signed off by a named owner, and egress enumerated beyond the obvious HTTP tool.
- **Anti-patterns to ban:** prompt-level mitigations presented as controls; treating an injection classifier as a broken leg; declaring a "read-only" agent safe (reading is the exfiltration channel); and a matrix with no owner on the accepted risks.

## Alternatives considered

- **A `lenses/agent.md` inside `threat-model`:** the closest call, and rejected on intake shape. `threat-model` consumes a design doc and produces STRIDE-per-trust-boundary; this consumes a *tool/permission manifest* and produces a per-capability trifecta matrix. Bolting it on would force one skill to carry two intake contracts and two output formats — and `threat-model`'s tier, examples, and quality bar are all written for the STRIDE artifact. The two are declared `related` so they compose instead.
- **Fold into `agent-loop-design`:** rejected — that skill's subject is the generate→verify→gate cycle. Security review of the capability surface is orthogonal; an agent can have a perfectly gated loop and still hold all three legs.
- **A generic "AI security checklist" skill:** rejected — a checklist without a per-path matrix produces the "we thought about security" artifact that changes no decision.
- **Do nothing:** rejected — this is the failure mode most likely to bite a skilldrop user in production, and the one the catalog is silent on.

## Decision

Implemented as proposed under `skills/agent-threat-model/` — `SKILL.md`, `reference.md` (egress catalog, trust test, ranked mitigation menu, injection-vector bank), `templates/agent-threat-model.md`, a worked `examples/support-triage-agent.md`, and `evals/`. Tier `heavy` in both `manifest.json` and `model-routing.json`; packs `ai-engineering` + `solution-architect`. One refinement during implementation: the ranked mitigation menu gained **structured output contracts** as a first-class fix (the privileged step accepts an enum or typed object, never free text), which turned out to be the mechanism that makes the split-agent pattern verifiable rather than aspirational.
