---
title: From signal to signed-off PRD — the product manager workflow
summary: A PM's full discovery-to-requirements session: sharpen the signal into a brief, test the narrative with a PR/FAQ, cascade OKRs, write the PRD, define metrics, critique before sharing.
kind: tutorial
---

# From signal to signed-off PRD — the product manager workflow

Six skills, one direction: from a vague signal to a PRD that has been tested, measured, and critiqued before anyone else reads it.

Install everything up front:

```bash
npx skilldrop-cli install --pack product-manager
```

---

## Step 1 — Structure the signal

**Skill:** `brief-intake`

A signal is not a requirement. Before writing anything, `brief-intake` interviews you to surface: the problem being solved, who it is for, what success looks like, and what is explicitly out of scope. A PRD written before this step is answering a question no one asked clearly.

**Say:** *"Run brief-intake for this initiative: [describe what you know]"*

**Output:** A structured brief. Every subsequent skill reads from this.

---

## Step 2 — Test the narrative

**Skill:** `prfaq`

The press release and FAQ format forces the question the PRD often skips: *does this narrative hold?* `prfaq` writes the customer-facing press release (what you would announce if it shipped) and a FAQ (the hard questions a sceptic would ask). If you cannot write a convincing press release, the PRD is not ready.

**Say:** *"Write a PR/FAQ for this initiative: [paste brief]"*

**Why prfaq comes before prd-draft:** A PRD is a specification investment — it takes time to write and creates expectation once shared. The PR/FAQ is cheap to write and tests the narrative before that investment is made. A narrative that fails the PR/FAQ test does not become a PRD; it goes back to the brief.

**Output:** Press release + FAQ. Review both. Anything the FAQ cannot answer is a gap in the brief.

---

## Step 3 — Connect to OKRs

**Skill:** `okr-cascade`

`okr-cascade` takes the initiative and the team's existing OKRs and produces the cascade: how this initiative contributes to which objective, and what the key result looks like. A PRD without OKR alignment is a feature without a business case.

**Say:** *"Cascade OKRs for this initiative against our current OKRs: [paste brief and current OKRs]"*

**Output:** Objective alignment + a proposed key result. This feeds into the success metrics step.

---

## Step 4 — Write the PRD

**Skill:** `prd-draft`

The PRD is now grounded: the brief gives it requirements, the PR/FAQ has tested the narrative, and the OKR cascade gives it a business case. `prd-draft` assembles from these inputs — it does not re-derive them.

**Say:** *"Write a PRD for this initiative using this brief, this PR/FAQ, and these OKRs: [paste all three]"*

**Output:** A complete PRD. Do not share it yet — it goes through metrics and critique first.

---

## Step 5 — Define success metrics

**Skill:** `success-metrics`

A PRD without metrics is a wish. `success-metrics` takes the PRD and the OKR cascade and produces the measurement plan: leading indicators, lagging indicators, guardrail metrics (things that must not regress), and the data source for each.

**Say:** *"Define success metrics for this PRD: [paste PRD and OKR cascade]"*

**Output:** A metrics table. Attach it to the PRD.

---

## Step 6 — Critique before sharing

**Skill:** `doc-critique`

`doc-critique` reviews the complete PRD for argument gaps, unsupported claims, internal inconsistencies, and sections that are vague enough to be interpreted differently by different readers. It does not rewrite — it flags, with enough specificity that you know exactly what to fix.

**Say:** *"Critique this PRD: [paste complete PRD with metrics]"*

**What doc-critique checks vs. a human review:**
- `doc-critique` runs before the human review, not instead of it. It catches structural issues (missing rationale, contradictory requirements, undefined terms) so the human reviewer can focus on the strategic and domain questions a model cannot assess.
- A human reviewer reading a PRD that has passed `doc-critique` spends their time on "is this the right thing to build?" not "what does this section mean?"

**Gate:** Any finding rated HIGH should be resolved before the PRD is shared. MEDIUM findings are your call; flag them if you leave them in.

---

## The full sequence

```
brief-intake → prfaq → okr-cascade → prd-draft → success-metrics → doc-critique
```

The narrative is tested before the PRD is written. The PRD is critiqued before it is shared. The sequence saves review cycles — every gate catches something cheap to fix now and expensive to fix after the PRD has set expectations.
