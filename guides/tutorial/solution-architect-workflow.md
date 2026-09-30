---
title: From brief to committed design — the solution architect workflow
summary: A full design session: capture the brief, draw the system, commit decisions as ADRs, write the design doc, threat-model it, gate with council review.
kind: tutorial
---

# From brief to committed design — the solution architect workflow

Six skills, strictly ordered. Each skill takes the output of the one before it as its primary input — running them out of order produces a weaker artifact because the context it depends on does not exist yet.

Install everything up front:

```bash
npx skilldrop-cli install --pack solution-architect
```

---

## Step 1 — Capture the brief

**Skill:** `brief-intake`

Before any diagram is drawn, the requirements need to be structured. `brief-intake` interviews the stakeholder (or you, acting as one) and produces a brief: the problem being solved, the constraints, the non-goals, and the open questions. A design that skips this step is solving a problem the architect assumed, not the problem that exists.

**Say:** *"Run brief-intake for this system: [describe the initiative]"*

**Output:** A structured brief. This is the input every subsequent skill reads.

---

## Step 2 — Visualise the system

**Skill:** `architecture-diagrams`

Takes the brief and produces the system diagram — components, boundaries, data flows, and the external dependencies. The diagram is not a deliverable; it is a thinking tool. Gaps in the diagram are gaps in the design.

**Say:** *"Draw architecture diagrams for the system described in this brief: [paste brief]"*

**Output:** Mermaid or PlantUML diagrams. Review them before moving on — anything that looks wrong is a decision waiting to be made explicit.

---

## Step 3 — Commit decisions as ADRs

**Skill:** `adr-generator`

Every significant decision made while designing the diagram becomes an Architecture Decision Record. An ADR names the decision, the alternatives considered, the forces that drove the choice, and the consequences. The design doc in step 4 references ADRs; without them the design doc is assertion without reasoning.

**Say:** *"Write ADRs for the decisions we made in this design: [paste diagram and list of decisions]"*

**Output:** One ADR per decision. Run this once per decision cluster, not once for the whole design.

**Why this order matters:** ADRs are written from the reasoning that produced the diagram, not from the diagram after the fact. If you write them after the design doc they become post-hoc justification.

---

## Step 4 — Write the design doc

**Skill:** `design-doc`

The design document assembles from what is now established: the brief (requirements and constraints), the diagrams (structure), and the ADRs (decisions and reasoning). It does not re-derive any of those — it synthesises them into a document a reviewer can read without the context of the session that produced it.

**Say:** *"Write a design doc for this system, using this brief, these diagrams, and these ADRs: [paste all three]"*

**Output:** A complete design document ready for review.

---

## Step 5 — Threat-model the design

**Skill:** `threat-model`

A security pass on the committed design. `threat-model` walks the data flows and trust boundaries in the diagram looking for: injection vectors, authentication gaps, authorisation bypass, data exposure, and denial-of-service surface. It produces a threat table — each threat with a severity rating and a mitigation.

**Say:** *"Threat-model this design: [paste design doc and diagrams]"*

**Gate:** Any HIGH-severity threat without a mitigation blocks the council review in step 6.

---

## Step 6 — Gate with council review

**Skill:** `council-review`

The stakeholder gate. `council-review` runs the design through a panel of synthetic reviewers — each representing a different stakeholder perspective (engineering, product, security, operations). A design that does not pass council is not committed.

**Say:** *"Run a council review on this design: [paste design doc, ADRs, and threat model]"*

**What council checks:**
- Does the design solve the problem in the brief?
- Are the ADRs complete and do the decisions hold?
- Has the threat model been addressed?
- Are the operational implications understood?

A finding from council is a revision, not a failure — the design goes back to the relevant step, not to the beginning.

---

## The full sequence

```
brief-intake → architecture-diagrams → adr-generator → design-doc → threat-model → council-review
```

The sequence is not arbitrary. Each step produces context the next one reads. A design that skips `brief-intake` is solving the wrong problem. A design that skips `adr-generator` has no auditable reasoning. A design that skips `threat-model` has not been reviewed for exploitability. A design that skips `council-review` has not been committed — it is still a draft.
