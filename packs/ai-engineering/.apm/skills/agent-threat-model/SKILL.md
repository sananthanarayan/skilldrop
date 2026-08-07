---
name: agent-threat-model
description: Threat-model an AI agent deployment against the lethal trifecta — private data, untrusted content, and an exfiltration vector — producing a per-capability matrix, a named architectural fix for every unsafe path, and a pre-launch checklist. Use before shipping an agent, when reviewing MCP server or tool permissions, when the user asks about prompt injection or data exfiltration risk, or when deciding whether an agent's capability surface is safe to expose.
---

# agent-threat-model

Answers one question about an agent deployment: **can text the agent reads cause it to send private data somewhere an attacker can see?** An LLM cannot reliably separate instructions from data, so any agent holding all three legs of the lethal trifecta — private data, untrusted content, an exfiltration vector — is compromised by construction, not by bug. The output is architectural: which leg gets broken, on which path, by which design change.

Complements `threat-model`, which runs STRIDE on the system the agent lives in. That model asks how the system is attacked; this one asks what the agent can be talked into doing. Run both on an agent that handles real data.

## How to respond

1. **Inventory the capability surface before scoring anything.** From the input — an agent description, MCP/tool config, system prompt, `agent-loop-design` output, or repo — extract four lists:
   - **Data reach** — everything the agent can read, *transitively*. A filesystem tool reaches every secret in `.env`; a database tool reaches every tenant the credential permits. Reach is what the credential allows, not what the feature intends.
   - **Content sources** — everything that puts tokens into the context window: user messages, web fetches, retrieved documents, file contents, tool results, PR comments, email, calendar invites, subagent output.
   - **Tools** — every callable, including the ones that feel inert (`read_file`, `search`, `fetch`).
   - **Egress paths** — every way bytes leave. This is the leg that gets missed; sweep [`reference.md`](reference.md) rather than listing the obvious HTTP tool.

   Ask at most 2 questions, and spend them on data reach and egress — a wrong boundary there invalidates the matrix. Everything else is tagged `[assumption]`.

2. **Classify each content source trusted or untrusted, defaulting to untrusted.** A source is trusted **only if every party who can write to it is already authorized to command the agent**. A shared team wiki fails this. A support ticket fails this. The agent's own earlier output fails it once untrusted content has entered the context. State the rule's verdict per source in one clause — ✅ *"Zendesk ticket body — untrusted; any customer can write it"*.

3. **Build the trifecta matrix, one row per capability path.** A path is a route from a content source, through the tools it can influence, to an egress. Mark each leg present/absent and rank with the shared markers:
   - 🟥 all three legs on one path, no gate — data theft is a design property; requires a broken leg
   - 🟧 all three legs, mitigated only by a human gate or an allowlist — the control is load-bearing and must be named
   - 🟨 two legs, third reachable by a plausible change (a new tool, a widened scope)
   - ⚪ one leg, or explicitly accepted with an owner

   If every row is 🟥, the paths weren't separated finely enough. If none are, check the egress sweep — it is usually incomplete.

4. **Break a leg on every 🟥, choosing from the ranked menu in [`reference.md`](reference.md).** Prefer the architectural fix over the procedural one: split the agent so the one reading untrusted content holds no privileged tools; remove the tool; allowlist egress destinations; gate the acting step on a human who sees the actual payload; narrow the credential. Each fix names *which leg it breaks* and how a reviewer verifies it — ✅ *"Retrieval subagent runs with no network tool and returns text only; verify by asserting the tool list is empty in its config test"*.

5. **Run the three sweeps that get skipped.** One finding or an explicit reasoned all-clear for each:
   - **Rendered egress** — markdown images, autolinked URLs, and HTML in any surface that renders agent output. An agent with no network tool still exfiltrates through an image the client fetches.
   - **Transitive reach** — the tool that reads the file that holds the credential that reaches the other system. Score reach at the end of the chain.
   - **Inherited capability** — subagents, tool-calling tools, and anything the agent can spawn. A quarantined reader that can invoke a privileged sibling is not quarantined.

6. **Write residual risk with owners.** Anything not fixed is accepted, in writing, by a **named role** with the trigger that would force revisiting it. An unowned residual risk is an unrecorded decision.

7. **Emit in one message**: capability inventory, the matrix, fixes per 🟥, the three sweeps, residual risk with owners, and a **pre-launch checklist** of what to verify before the agent faces real data. End with the revisit trigger — the model is stale the moment a tool, a content source, or a credential scope is added.

**Non-interactive runs:** unstated capabilities are tagged `[assumption]` and modeled at their worst plausible scope. If no tool list, data reach, or content source can be established at all, emit `BLOCKED: need the agent's tool/permission inventory` — with nothing to inventory there is no model, and a fabricated one is worse than none.

## Useful references in this skill

- [`reference.md`](reference.md) — the egress catalog (the sweep for step 1), the trust test for content sources, the ranked mitigation menu, and the injection-vector bank per source type
- [`templates/agent-threat-model.md`](templates/agent-threat-model.md) — output skeleton
- [`examples/support-triage-agent.md`](examples/support-triage-agent.md) — worked example: a Zendesk triage agent, 4 paths, 2 🟥, one split that fixes both

## Quality bar

- **Every capability path is scored on all three legs.** A row with a blank leg wasn't analyzed, it was skipped.
- **No prompt-level mitigation is presented as a control.** "The system prompt instructs the model to ignore injected instructions" mitigates nothing — it is precisely what the attack defeats. It may appear as defense in depth, never as the broken leg.
- **No classifier is a broken leg either.** Injection detectors raise cost for the attacker; they do not remove a leg. Architecture beats instructions.
- **Egress is enumerated past the network tool.** A model that lists only `http_request` failed the sweep — rendered markdown, error text, logs, and file writes are all channels.
- **Every 🟥 is broken or signed off** by a named role with a revisit trigger. No silent acceptance.
- **Every fix has a verification step** a reviewer can actually run — a config assertion, a test, an observed denial.
- **"Read-only" is never a safety claim.** Reading is how data reaches the attacker; the question is only where it goes next.

## When to use this skill

- ✅ Before shipping an agent that touches private data, internal systems, or customer content
- ✅ Reviewing which MCP servers or tools an agent should be granted
- ✅ "Could someone prompt-inject this?" / "Can this agent leak our data?"
- ✅ Auditing an existing agent after a new tool, integration, or content source is added
- ✅ Alongside `subagent-design` when deciding whether a task needs a quarantined reader

## When NOT to use this skill

- ❌ STRIDE on the surrounding system's architecture — that's `threat-model`
- ❌ Reviewing written code for vulnerabilities — that's `devils-advocate` or `sonar-review`
- ❌ Runaway loops, token burn, or infinite retries — that's `agent-budget` (a cost incident, not a security one)
- ❌ Output quality, hallucination, or eval design — that's `llm-eval-harness`
- ❌ After a confirmed leak — that's `postmortem-generator`

## Anti-patterns to avoid

- ❌ **Trusting the system prompt as a boundary.** Instructions in the prompt and instructions in a fetched web page arrive as the same tokens. Anything that relies on the model choosing correctly between them is a wish.
- ❌ **Declaring a read-only agent safe.** Read-only means it can't write to *your* systems. It says nothing about what it hands to an attacker.
- ❌ **Listing tools instead of paths.** The trifecta is a property of a route through the agent, not of any single tool. `fetch` is fine alone and lethal next to a secrets file.
- ❌ **Counting a human gate as a fix without describing what the human sees.** Approving "the agent wants to call `send_email`" catches nothing; approving the rendered recipient and body catches the exfiltration.
- ❌ **Modeling the intended flow only.** Error paths, retries, and the debug logging surface all carry data and are rarely scoped.
- ❌ **A matrix with no owner on the accepted rows.** That is a document that files the risk, not one that assigns it.
