# Guides

Longer-form material that used to live in the README. Split by
[Diátaxis](https://diataxis.fr) **kind** — declared in each page's frontmatter, not implied by
its directory, so the tree stays shallow.

| Kind | Answers |
|---|---|
| **tutorial** | "Let me learn by doing something real." |
| **how-to** | "I have a goal — what are the steps?" |
| **reference** | "What exactly does this field/command do?" |
| **explanation** | "Why is it built this way?" |

New here? Start with the [operating model](explanation/operating-model.md): the five stages, the gate that ends each one, and the pack that helps there.

## tutorial

- [Follow one change through the loops](tutorial/follow-a-change-through-the-loops.md) — one realistic change walked from a complaint to a closed incident, showing what each gate refuses
- [From complaint to closed incident](tutorial/complaint-to-closed-incident.md) — End-to-end: complaint → discover loop → operate loop → closed incident with updated runbook
- [From idea to shipped feature](tutorial/idea-to-shipped-feature.md) — End-to-end: idea → all five lifecycle loops → shipped feature with postmortem
- [Dev-team workflow](tutorial/dev-team-workflow.md) — story → implementation → review panel → release notes
- [Solution architect workflow](tutorial/solution-architect-workflow.md) — brief → diagrams → ADRs → design doc → threat model → council gate
- [Product manager workflow](tutorial/product-manager-workflow.md) — signal → PR/FAQ → OKRs → PRD → metrics → critique gate
- [AI engineering workflow](tutorial/ai-engineering-workflow.md) — use-case triage → readiness → loop design → threat model → evals → usage report
- [A why question to an answer the evidence carries](tutorial/why-question-to-evidence.md) — the research loop: plan → cited synthesis → rival explanations → evidence-strength gate
- [From a risky change to a risk position its owner signs](tutorial/risky-change-to-signed-risk.md) — the comply loop: register → DPIA → evidence map → script check → owner sign-off
- [From a dashboard request to numbers people can defend](tutorial/dashboard-request-to-defensible-numbers.md) — the measure loop: spec and cut list → SQL review → metric owner sign-off
- [From an agreed PRD to a tracker that stays honest](tutorial/prd-to-honest-tracker.md) — PRD → Jira import → backlog triage → weekly status from counts → drift check
- [From a Terraform module to a plan you can safely apply](tutorial/module-to-safe-apply.md) — a module with secure defaults, then a plan review that catches a hidden database replace
- [Write a skill your whole team can install, then review one before you trust it](tutorial/write-and-review-a-skill.md) — skill-author → lint against siblings → review a teammate's unsafe skill
- [One Markdown draft, every reader's format](tutorial/one-draft-every-format.md) — Markdown → Word, Excel and HTML, a diagram checked, and a reply brought back, with what each drops
- [From an unreadable page to a service people can use](tutorial/page-to-service.md) — rewrite a council page from user needs, write the form's words, and blueprint the service behind it

## how-to

- [Install skills, packs and loops](how-to/install.md) — every route: the CLI for any IDE, the Claude Code plugin marketplace, and by hand
- [Install a skill into your IDE](how-to/install-per-ide.md) — per-IDE steps for every target, plus dependency installs
- [Install a profile](how-to/profiles.md) — named bundles of packs, agents, and loops in one command
- [Author a new skill](how-to/author-a-skill.md) — what a skill must contain and what gates it
- [Author a new loop](how-to/author-a-loop.md) — the closed `loop.json` contract and the gate rules
- [Wire a skill to an event](how-to/wire-a-hook.md) — opt-in hooks, projected per target
- [Publish your own catalogue](how-to/publish-a-catalogue.md) — make `skilldrop --from <you>` work
- [Release a change](how-to/release-a-change.md) — the release loop: a rollout with a way back, a readiness check on evidence, and your go/no-go call
- [Upgrade installed skills](how-to/upgrade-skills.md) — keep what you have installed current; files you edited are kept and the new version lands beside them as `.upstream`
- [Benchmark skills against the agent without them](how-to/benchmark-skills.md) — each eval run with the skill and without it: the lift, a blind preference from two judges, and the cost
- [Measure your loops](how-to/measure-your-loops.md) — the opt-in, local-only run log, and which gates pass first time
- [Run a skill in CI](how-to/run-a-skill-in-ci.md) — the GitHub Action: a skill on every pull request, results in the job summary, optional fail on a verdict
- [Roll out across your org](how-to/enterprise-distribution.md) — bootstrap the hosted marketplace for every machine in one command
- [Contain a skill's reach](how-to/contain-skills.md) — run a project's shell commands in Claude Code's sandbox, limited to what its skills declare
- [Govern skills across an organisation](how-to/govern-skills.md) — a policy the installer enforces, an inventory of every machine, and an audit log that shows if it was edited
- [Use with MCP servers](how-to/use-with-mcp-servers.md) — which servers pair with which skills, adding one in each tool, and the security rules
- [Use with Jira](how-to/integrate-with-jira.md) — bug triage, story splitting, implementation loops, and release notes from Jira tickets
- [Use with GitHub Projects](how-to/integrate-with-github-projects.md) — implementation loops, review gates, and release notes linked to GitHub issues
- [Use with Figma](how-to/integrate-with-figma.md) — generate diagrams for FigJam, reverse-engineer decisions from mockups
- [Use with Linear](how-to/integrate-with-linear.md) — triage, story splitting, implementation tracking, and release notes from Linear issues
- [Supply credentials to skills](how-to/supply-credentials.md) — how to set FIGMA_TOKEN, SONAR_TOKEN, and other env vars locally, in CI, and via secret managers

## reference

- [Every skill, by category](reference/skill-catalogue.md) — all the skills, one line each, plus the anatomy every skill folder shares
- [The loops, stage by stage](reference/loops.md) — each loop's stages, gates and generated diagram
- [The loop contract](reference/loop-contract.md) — the closed `loop.json` fields, gate ids and verdict rules, what `LOOP.md` carries, and how a loop is registered and checked
- [The skill contract](reference/skill-contract.md) — what a new skill folder must contain, its catalogue entries, and what `validate.py` checks
- [Install options](reference/install-options.md) — every CLI install command and flag, the plugin marketplace's plugins and how they are built, and the reviewer subagents
- [Install targets and dependencies](reference/install-targets.md) — where each target writes skills and subagents, by-hand steps per tool, what `--local` does, and per-skill dependency installs
- [Updates and the install ledger](reference/update-and-ledger.md) — what outdated, update, diff and doctor compare and decide: the ledger, `.upstream` rules, flags, edge cases
- [The skilldrop GitHub Action](reference/ci-action.md) — every input and output of the Action, what it never runs, good fits, cost and privacy
- [Benchmark options and report](reference/benchmark-options.md) — every `run_bench.py` flag, how each run is isolated, what it writes, and what each number in the report means
- [MCP servers and skills](reference/mcp-servers.md) — which MCP servers pair with which skills and loops, config for each tool, security rules and troubleshooting
- [Skills that ship scripts](reference/skills-with-scripts.md) — every skill with scripts and what each declares it needs, and how to invoke a skill
- [skilldrop and the OWASP Top 10s](reference/owasp-mapping.md) — what skilldrop covers in the Agentic Skills Top 10 and LLM Top 10 2025, and the gaps
- [Policy file and audit log](reference/policy-and-audit.md) — every field of the organisation policy, how it fails, and the audit log and inventory formats

## Per pack

A how-to and a reference page for every pack, generated from the pack's own files by
`build_pack_guides.py`.

<!-- pack-guides:start -->
| Pack | How-to | Reference |
|---|---|---|
| Core | [Use the Core pack](how-to/packs/use-the-core-pack.md) | [Core pack reference](reference/packs/pack-core.md) |
| Solution architect | [Use the Solution architect pack](how-to/packs/use-the-solution-architect-pack.md) | [Solution architect pack reference](reference/packs/pack-solution-architect.md) |
| Product manager | [Use the Product manager pack](how-to/packs/use-the-product-manager-pack.md) | [Product manager pack reference](reference/packs/pack-product-manager.md) |
| Dev team | [Use the Dev team pack](how-to/packs/use-the-dev-team-pack.md) | [Dev team pack reference](reference/packs/pack-dev-team.md) |
| SRE / on-call | [Use the SRE / on-call pack](how-to/packs/use-the-sre-oncall-pack.md) | [SRE / on-call pack reference](reference/packs/pack-sre-oncall.md) |
| Stakeholder comms | [Use the Stakeholder comms pack](how-to/packs/use-the-stakeholder-comms-pack.md) | [Stakeholder comms pack reference](reference/packs/pack-stakeholder-comms.md) |
| Design | [Use the Design pack](how-to/packs/use-the-design-pack.md) | [Design pack reference](reference/packs/pack-design.md) |
| AI engineering | [Use the AI engineering pack](how-to/packs/use-the-ai-engineering-pack.md) | [AI engineering pack reference](reference/packs/pack-ai-engineering.md) |
| API builder | [Use the API builder pack](how-to/packs/use-the-api-builder-pack.md) | [API builder pack reference](reference/packs/pack-api-builder.md) |
| Converters | [Use the Converters pack](how-to/packs/use-the-converters-pack.md) | [Converters pack reference](reference/packs/pack-converters.md) |
| Experience design | [Use the Experience design pack](how-to/packs/use-the-experience-design-pack.md) | [Experience design pack reference](reference/packs/pack-experience-design.md) |
| Research | [Use the Research pack](how-to/packs/use-the-research-pack.md) | [Research pack reference](reference/packs/pack-research.md) |
| Trackers | [Use the Trackers pack](how-to/packs/use-the-trackers-pack.md) | [Trackers pack reference](reference/packs/pack-trackers.md) |
| Data and analytics | [Use the Data and analytics pack](how-to/packs/use-the-data-analytics-pack.md) | [Data and analytics pack reference](reference/packs/pack-data-analytics.md) |
| Governance, risk and compliance | [Use the Governance, risk and compliance pack](how-to/packs/use-the-grc-pack.md) | [Governance, risk and compliance pack reference](reference/packs/pack-grc.md) |
| Infrastructure as code | [Use the Infrastructure as code pack](how-to/packs/use-the-infra-as-code-pack.md) | [Infrastructure as code pack reference](reference/packs/pack-infra-as-code.md) |
| Frontend | [Use the Frontend pack](how-to/packs/use-the-frontend-pack.md) | [Frontend pack reference](reference/packs/pack-frontend.md) |
| Skill engineering | [Use the Skill engineering pack](how-to/packs/use-the-skill-engineering-pack.md) | [Skill engineering pack reference](reference/packs/pack-skill-engineering.md) |
| Job applications | [Use the Job applications pack](how-to/packs/use-the-career-pack.md) | [Job applications pack reference](reference/packs/pack-career.md) |
<!-- pack-guides:end -->

### Per skill

One how-to for every skill: how to install it, the requests that route to it, what a good result looks like, and what to use instead.

<!-- skill-guides:start -->
| Pack | Skills |
|---|---|
| Core | [brief-intake](how-to/skills/use-brief-intake.md), [council-review](how-to/skills/use-council-review.md), [doc-critique](how-to/skills/use-doc-critique.md), [output-hygiene](how-to/skills/use-output-hygiene.md) |
| Solution architect | [adr-generator](how-to/skills/use-adr-generator.md), [api-contract-draft](how-to/skills/use-api-contract-draft.md), [architecture-diagrams](how-to/skills/use-architecture-diagrams.md), [data-contract](how-to/skills/use-data-contract.md), [design-doc](how-to/skills/use-design-doc.md), [event-contract-draft](how-to/skills/use-event-contract-draft.md), [figma-diagrams](how-to/skills/use-figma-diagrams.md), [interactive-diagram](how-to/skills/use-interactive-diagram.md), [nfr-spec](how-to/skills/use-nfr-spec.md), [reverse-architecture](how-to/skills/use-reverse-architecture.md), [threat-model](how-to/skills/use-threat-model.md) |
| Product manager | [business-case](how-to/skills/use-business-case.md), [feedback-synthesis](how-to/skills/use-feedback-synthesis.md), [lean-canvas](how-to/skills/use-lean-canvas.md), [okr-cascade](how-to/skills/use-okr-cascade.md), [prd-draft](how-to/skills/use-prd-draft.md), [prfaq](how-to/skills/use-prfaq.md), [requirements-interview](how-to/skills/use-requirements-interview.md), [strategy-analysis](how-to/skills/use-strategy-analysis.md), [success-metrics](how-to/skills/use-success-metrics.md), [user-journey-map](how-to/skills/use-user-journey-map.md) |
| Dev team | [accessibility-audit](how-to/skills/use-accessibility-audit.md), [agents-md-generator](how-to/skills/use-agents-md-generator.md), [behaviour-equivalence](how-to/skills/use-behaviour-equivalence.md), [bug-triage](how-to/skills/use-bug-triage.md), [codebase-tour](how-to/skills/use-codebase-tour.md), [dependency-upgrade-review](how-to/skills/use-dependency-upgrade-review.md), [devils-advocate](how-to/skills/use-devils-advocate.md), [feature-implement-loop](how-to/skills/use-feature-implement-loop.md), [launch-readiness](how-to/skills/use-launch-readiness.md), [migration-plan](how-to/skills/use-migration-plan.md), [pr-description-writer](how-to/skills/use-pr-description-writer.md), [pre-merge-review](how-to/skills/use-pre-merge-review.md), [refactor-plan](how-to/skills/use-refactor-plan.md), [release-notes](how-to/skills/use-release-notes.md), [rollout-plan](how-to/skills/use-rollout-plan.md), [sonar-onboard](how-to/skills/use-sonar-onboard.md), [sonar-review](how-to/skills/use-sonar-review.md), [tech-debt-register](how-to/skills/use-tech-debt-register.md), [test-plan-generator](how-to/skills/use-test-plan-generator.md), [user-story-splitter](how-to/skills/use-user-story-splitter.md) |
| SRE / on-call | [capacity-cost-model](how-to/skills/use-capacity-cost-model.md), [cloud-cost-review](how-to/skills/use-cloud-cost-review.md), [delivery-metrics-report](how-to/skills/use-delivery-metrics-report.md), [incident-comms](how-to/skills/use-incident-comms.md), [observability-plan](how-to/skills/use-observability-plan.md), [postmortem-generator](how-to/skills/use-postmortem-generator.md), [runbook-generator](how-to/skills/use-runbook-generator.md), [slo-spec](how-to/skills/use-slo-spec.md) |
| Stakeholder comms | [audience-profile](how-to/skills/use-audience-profile.md), [decision-log](how-to/skills/use-decision-log.md), [exec-summary](how-to/skills/use-exec-summary.md), [guide-builder](how-to/skills/use-guide-builder.md) |
| Design | [brand-kit](how-to/skills/use-brand-kit.md), [deck-builder](how-to/skills/use-deck-builder.md), [marketing-flyer](how-to/skills/use-marketing-flyer.md), [slide-outliner](how-to/skills/use-slide-outliner.md) |
| AI engineering | [agent-adoption-stage](how-to/skills/use-agent-adoption-stage.md), [agent-budget](how-to/skills/use-agent-budget.md), [agent-config-review](how-to/skills/use-agent-config-review.md), [agent-incident-response](how-to/skills/use-agent-incident-response.md), [agent-loop-design](how-to/skills/use-agent-loop-design.md), [agent-threat-model](how-to/skills/use-agent-threat-model.md), [ai-adoption-rollout](how-to/skills/use-ai-adoption-rollout.md), [ai-readiness-assessment](how-to/skills/use-ai-readiness-assessment.md), [ai-usage-policy](how-to/skills/use-ai-usage-policy.md), [ai-usage-report](how-to/skills/use-ai-usage-report.md), [ai-use-case-triage](how-to/skills/use-ai-use-case-triage.md), [llm-eval-harness](how-to/skills/use-llm-eval-harness.md), [mcp-pairing](how-to/skills/use-mcp-pairing.md), [subagent-design](how-to/skills/use-subagent-design.md) |
| API builder | [eval-harness-generator](how-to/skills/use-eval-harness-generator.md), [prompt-caching-advisor](how-to/skills/use-prompt-caching-advisor.md), [token-budget-estimator](how-to/skills/use-token-budget-estimator.md), [tool-use-schema-writer](how-to/skills/use-tool-use-schema-writer.md) |
| Converters | [file-to-markdown](how-to/skills/use-file-to-markdown.md), [md-to-confluence](how-to/skills/use-md-to-confluence.md), [md-to-docx](how-to/skills/use-md-to-docx.md), [md-to-html](how-to/skills/use-md-to-html.md), [md-to-pptx](how-to/skills/use-md-to-pptx.md), [md-to-xlsx](how-to/skills/use-md-to-xlsx.md), [mermaid-render](how-to/skills/use-mermaid-render.md) |
| Experience design | [content-design](how-to/skills/use-content-design.md), [design-system-spec](how-to/skills/use-design-system-spec.md), [information-architecture](how-to/skills/use-information-architecture.md), [service-blueprint](how-to/skills/use-service-blueprint.md), [ux-writing](how-to/skills/use-ux-writing.md) |
| Research | [hypothesis-comparison](how-to/skills/use-hypothesis-comparison.md), [research-plan](how-to/skills/use-research-plan.md), [source-synthesis](how-to/skills/use-source-synthesis.md) |
| Trackers | [backlog-triage](how-to/skills/use-backlog-triage.md), [team-status-report](how-to/skills/use-team-status-report.md), [tracker-brief-sync](how-to/skills/use-tracker-brief-sync.md) |
| Data and analytics | [dashboard-spec](how-to/skills/use-dashboard-spec.md), [sql-review](how-to/skills/use-sql-review.md) |
| Governance, risk and compliance | [dpia](how-to/skills/use-dpia.md), [risk-register](how-to/skills/use-risk-register.md), [security-questionnaire-response](how-to/skills/use-security-questionnaire-response.md), [soc2-evidence-map](how-to/skills/use-soc2-evidence-map.md) |
| Infrastructure as code | [terraform-module](how-to/skills/use-terraform-module.md), [terraform-plan-review](how-to/skills/use-terraform-plan-review.md) |
| Frontend | [rendering-strategy](how-to/skills/use-rendering-strategy.md), [web-performance-review](how-to/skills/use-web-performance-review.md) |
| Skill engineering | [skill-author](how-to/skills/use-skill-author.md), [skill-review](how-to/skills/use-skill-review.md) |
| Job applications | [application-form-answers](how-to/skills/use-application-form-answers.md), [cover-letter](how-to/skills/use-cover-letter.md), [job-fit-analysis](how-to/skills/use-job-fit-analysis.md), [resume-tailor](how-to/skills/use-resume-tailor.md), [role-shortlist](how-to/skills/use-role-shortlist.md) |
<!-- skill-guides:end -->

## explanation

- [Operating model](explanation/operating-model.md) — the five stages, the gate that ends each one, where the agent waits for you, and the packs for any stage
- [Why loops](explanation/loops.md) — why sequencing is its own primitive, and why five loops
- [Cost-aware model routing](../MODEL-ROUTING.md) — abstract tiers and the provider map
- [What the benchmark showed](explanation/what-the-benchmark-showed.md) — the gain on skills' own checks, the blind preference, the held-out test that the revised skills failed, and what the winners share
- [Does the agent invent your resume?](explanation/resume-fabrication-comparison.md) — 14 resume and cover-letter requests with the career skills and without: what each added that the person never said

Architecture and the enforcement model: [ARCHITECTURE.md](../ARCHITECTURE.md).
Contributor rules and the pre-commit checklist: [AGENTS.md](../AGENTS.md).
