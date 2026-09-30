---
title: From use-case to deployed agent — the AI engineering workflow
summary: End-to-end AI adoption: triage the use case, assess org readiness, design the loop and agents, threat-model the system, build the evals, measure what shipped.
kind: tutorial
---

# From use-case to deployed agent — the AI engineering workflow

Seven skills. The first two are stop gates — they exist to kill bad investments early. The rest build the system that will actually ship.

Install everything up front:

```bash
npx skilldrop-cli install --pack ai-engineering
```

---

## Step 1 — Triage the use case

**Skill:** `ai-use-case-triage`

Most AI use cases fail not because the model is wrong but because the use case was wrong to begin with — too ambiguous, too high-stakes for current model reliability, or solving a problem that does not actually exist. `ai-use-case-triage` scores the use case on: clarity, feasibility, reversibility of errors, and value if it works. Use cases that score poorly stop here.

**Say:** *"Triage this AI use case: [describe what you want the agent to do]"*

**Gate:** A LOW score is a stop signal. The use case either needs to be redefined or abandoned. Continuing past a LOW score wastes the readiness assessment, the design, and the build.

---

## Step 2 — Assess org readiness

**Skill:** `ai-readiness-assessment`

Even a strong use case fails if the organisation is not ready to support it. `ai-readiness-assessment` checks: data availability and quality, existing tooling and integrations, the team's ability to monitor and intervene, and the process changes the deployment requires. A readiness gap does not kill the project — it surfaces what needs to be true before the system can ship safely.

**Say:** *"Assess our readiness to deploy this use case: [paste triage output and describe the org context]"*

**Why triage and readiness come first:** Designing an agentic system is expensive. A system that passes design and build but cannot be deployed because the data is not there or the team cannot monitor it has wasted every hour spent on it. These two gates are cheap relative to the work they prevent.

---

## Step 3 — Design the loop

**Skill:** `agent-loop-design`

The agentic loop is the sequence of stages the agent runs: what it reads, what it writes, where it calls tools, and where a human must intervene before the loop continues. `agent-loop-design` produces the loop specification: stages, tools per stage, human gates, and the cap (maximum iterations before the loop stops and escalates).

**Say:** *"Design the agent loop for this use case: [paste triage and readiness outputs]"*

**Output:** A loop specification with stages, tool bindings, gate conditions, and cap. This is the input to subagent design.

---

## Step 4 — Design the agents

**Skill:** `subagent-design`

Complex loops delegate to specialist subagents — each one focused on a single task so its behaviour is auditable and replaceable. `subagent-design` takes the loop specification and produces the agent definitions: what each agent knows, what tools it has access to, what it is explicitly prohibited from doing, and how the orchestrator delegates to it.

**Say:** *"Design the subagents for this loop: [paste loop specification]"*

**Output:** One agent definition per subagent. Review the tool access lists carefully — an agent with more tools than it needs for its stage is a security surface, not a capability.

---

## Step 5 — Threat-model the system

**Skill:** `agent-threat-model`

**This is a gate, not a suggestion.** Agentic systems have a threat surface that static software does not: prompt injection (an adversary controls the agent's context through data it reads), tool misuse (the agent calls a tool with arguments that cause unintended side effects), and data exfiltration (the agent reads sensitive data and writes it somewhere it should not go). `agent-threat-model` walks every stage of the loop looking for these vectors and produces a threat table with severity ratings and mitigations.

**Say:** *"Threat-model this agentic system: [paste loop spec, agent definitions, and tool list]"*

**Gate:** Any HIGH-severity threat without a mitigation blocks the eval build. A system that passes threat-modelling with open HIGH-severity threats is a system that will be exploited.

---

## Step 6 — Build the evals

**Skill:** `llm-eval-harness`

Evals are built before deployment, not after. Without them there is no way to know whether a model change, a prompt edit, or a new tool integration regressed the system's behaviour. `llm-eval-harness` produces the eval suite: test cases (input → expected output), assertions, negative cases (inputs that should NOT trigger the behaviour), and the harness configuration.

**Say:** *"Build an eval harness for this agent system: [paste loop spec, agent definitions, and acceptance criteria]"*

**What the harness gates:** Every deployment goes through the harness. If the pass rate drops below the threshold defined in the harness, the deployment does not proceed. The threshold is set during this step, not during the incident that triggers it.

---

## Step 7 — Measure what shipped

**Skill:** `ai-usage-report`

After deployment, `ai-usage-report` produces the measurement report: how often the system ran, what it produced, where it escalated to humans, what the error rate was, and what the cost was. This is the evidence base for the next investment decision — whether to extend the system, fix it, or retire it.

**Say:** *"Write an AI usage report for this deployed system: [describe what data you have — runs, outputs, escalations, costs]"*

---

## The full sequence

```
ai-use-case-triage → ai-readiness-assessment → agent-loop-design → subagent-design → agent-threat-model → llm-eval-harness → ai-usage-report
```

The sequence front-loads the kills. A use case that fails triage does not consume a readiness assessment. A system that fails threat-modelling does not consume an eval build. The expensive work happens only after the cheap gates pass.
