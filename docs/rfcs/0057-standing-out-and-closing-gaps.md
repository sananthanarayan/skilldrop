---
rfc: 0057
title: Skills, a loop and agents that close the gaps with agent-ready-repo
status: implemented
date: 2026-10-20
author: sanjay-ananth
---

# RFC-0057: Skills, a loop and agents that close the gaps with agent-ready-repo

## Problem / use case

A live comparison with eugenelim/agent-ready-repo on 2026-10-20 (26 packs, about 130 skills, 17
subagents) found two things to act on.

**Where it is ahead:**
- a frontend engineering pack;
- event contracts;
- PowerPoint and Confluence output, and Outlook mail input;
- lean canvas;
- SLO definition;
- more review subagents, including one that adjudicates a panel's findings.

**What October's news made timely:**
- **Long-horizon code migration** is the headline (Gemini 4 Argon; OpenAI reporting 97.9% on
  legacy modernisation). No catalogue proves a migration changed nothing.
- **Agent tooling incidents:** OpenCode's console was breached on 19 October and stolen API
  keys ran up users' bills. Exposed Cairn agent installs were used for intrusions.
- **Task-scoped agent permissions:** Microsoft shipped them, and Claude Code added
  plugin-required human approval.
- **LLM-judge audits:** Google published evaluator-audit guidance on the same day.

## Fit check

Each new skill makes one artifact, installs as a plain folder, and uses only standard-library
Python for its scripts. Each one ships only if blind judges prefer it to plain Claude Code on
held-out evals (RFC-0041, RFC-0042). The new pack, `frontend`, holds skills no existing pack
fits. The loop and the agents follow their own contracts (RFC-0028, RFC-0012).

## Proposal

Twelve skills were drafted. Ten were admitted, and two were held back for revision.

| Skill | Pack | Admitted |
|---|---|---|
| `behaviour-equivalence` | dev-team | yes |
| `event-contract-draft` | solution-architect | yes |
| `slo-spec` | sre-oncall | yes |
| `lean-canvas` | product-manager | yes |
| `agent-config-review` | ai-engineering | yes |
| `agent-incident-response` | ai-engineering | yes, after one revision |
| `web-performance-review` | frontend (new) | yes |
| `rendering-strategy` | frontend (new) | yes |
| `md-to-pptx` | converters | yes |
| `md-to-confluence` | converters | yes |
| `bundle-size-review` | frontend | no; being revised |
| `judge-audit` | ai-engineering | no; being revised |

**Also built:**
- **A `modernize` loop:**
  - It surveys the component, plans the work, and records the old system's behaviour before
    anything is rebuilt.
  - After the rebuild, `behaviour-equivalence`'s diff script decides G10.
  - A person decides the cutover at G10.1.
- **`file-to-markdown` reads `.eml` and Outlook `.msg`.** `.msg` is read with a bounded,
  standard-library reader for Outlook's file format, tested on real Outlook files kept out of
  the repo for licensing reasons.
- **Three review agents:** `test-reviewer`, `docs-reviewer` and `finding-adjudicator`.
- **`api-contract-draft`** now hands event contracts to `event-contract-draft`.
- **The link check** no longer reads eval fixtures, whose broken links are often the trap.

**Not taken:**
- **A code graph** (agent-ready-repo's `code-intelligence` needs an external Rust binary). It
  waits on the owner's decision about a context-graph skill.
- **Jira Align**, which is too narrow to test here.

## Alternatives considered

- **Copy agent-ready-repo's eight-skill frontend pack.** Most of those skills are formats a
  plain agent produces unprompted, which RFC-0046 retired. The skills taken here compute what
  a plain agent estimates.
- **Ship every drafted skill.** The admission bar exists because two of these, on first draft,
  lost to plain Claude Code in every pair.

## Decision

Accepted. Measured on two held-out evals per skill, written blind from the description, two
trials, two judges (`claude-sonnet-5-5`, `claude-opus-5-5`), on `claude-sonnet-5`:

| Skill | Pairs won, judge 1 | Judge 2 | Checks met, skill | Without |
|---|---|---|---|---|
| `slo-spec` | 4 of 4 | 4 of 4 | 56% | 53% |
| `rendering-strategy` | 4 of 4 | 4 of 4 | 75% | 66% |
| `web-performance-review` | 3 of 4 | 4 of 4 | 44% | 38% |
| `behaviour-equivalence` | 3 of 4 | 3 of 4 | 66% | 53% |
| `lean-canvas` | 3 of 4 | 3 of 4 | 72% | 41% |
| `md-to-confluence` | 3 of 4 | 3 of 4 | 59% | 19% |
| `agent-incident-response`, revised, on new evals 6 and 7 | 3 of 4 | 3 of 4 | 41% | 31% |
| `agent-config-review` | 3 of 4 | 2 of 4 | 53% | 44% |
| `event-contract-draft` | 2 of 4 | 3 of 4 | 50% | 47% |
| `md-to-pptx` | 2 of 4 | 2 of 4 | 94% | 69% |

**`md-to-pptx` and `event-contract-draft` clear the bar exactly**, so their next revisions
need evals of their own.

**Not admitted:**
- **`bundle-size-review`** (0 of 4 with both judges). It said a repository had no browserslist
  when it had a `.browserslistrc`. It also led with estimated gzip sizes instead of the exact
  bytes in the stats file, and mixed KB and KiB.
- **`judge-audit`**:
  - **First draft (0 of 4 with both judges):** it used unweighted kappa on a 1–5 scale. It
    also missed that the grader over-scored only the variant being tested.
  - **Revised (3 of 4 and 1 of 4):** it fixed both. Judge 2 then penalised release thresholds
    the skill imposed that weren't in the data, and run-1 figures presented as if both runs
    were merged.

Benchmark spend was $32.26.

## Revision: `bundle-size-review` and `judge-audit` (0.16.37)

- **`bundle-size-review`**, revised once:
  - It reads the repository around the stats file before concluding anything: browser
    targets, the bundler config, installed versions, and the source that imports each heavy
    package.
  - It leads with exact byte sizes in one unit (kB = 1000), and gives a compressed size only
    when it was measured.
  - It answers the question first, and checks that fixes suit the installed versions.
- **`judge-audit`**, revised twice:
  - The second draft added weighted kappa for 1–5 scores, and a per-variant breakdown so a
    judge biased toward one arm shows.
  - The third draft:
    - checks only against the user's own gate and invents no pass mark;
    - names a pick when asked which judge to use;
    - reports each run on its own, joined by item id;
    - reports precision and recall, with intervals, for a rare class.

Measured on two new held-out evals each, written blind, two trials, the same two judges:

| Skill | Evals | Pairs won, judge 1 | Judge 2 | Checks met, skill | Without |
|---|---|---|---|---|---|
| `bundle-size-review` | 6 and 7 | 3 of 4 | 3 of 4 | 31% | 31% |
| `judge-audit` | 8 and 9 | 2 of 4 | 2 of 4 | 41% | 19% |

Both clear the bar. **`judge-audit` clears it exactly, after three drafts**, so its next
revision needs evals of its own. **`bundle-size-review` meets no more checks than the plain
agent;** the judges preferred it for exact figures and safe fixes. Re-test spend was $9.47.
