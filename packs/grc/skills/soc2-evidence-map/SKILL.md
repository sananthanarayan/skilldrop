---
name: soc2-evidence-map
description: Map an organisation's controls to the SOC 2 Trust Services Criteria in scope (Security always, plus Availability, Confidentiality, Processing Integrity or Privacy if chosen), and for each control list the evidence an auditor will ask for, the system it lives in, the owner, how often it is produced, and the gaps — distinguishing Type I (designed and in place at a date) from Type II (operating over a period, sampled from a full population) — as a table and a CSV the team can work from. Use when the user is preparing for a SOC 2 audit or readiness assessment, says "SOC 2 evidence", "map our controls to the TSC", "what will the auditor ask for", "SOC 2 gap analysis".
---

# soc2-evidence-map

You turn a controls list, or a description of how the company runs its systems, into the
working document a SOC 2 project runs on: each control mapped to the criteria it addresses,
the exact evidence the auditor will request, where that evidence comes from, who produces
it, how often, and what is missing. The output is a Markdown summary and a CSV. You prepare
material for the company's compliance lead and its auditor to review; it is not audit
advice, and only the service auditor decides what evidence is sufficient.

## How to respond

1. **Ask once for what is missing, in one message.** Take what is already given. Ask for at
   most two things, and say what you will assume for the rest:
   - **Scope:** which Trust Services Categories (Security is always in scope), the system
     or product being reported on, and **Type I or Type II** with the date or period.
     *Default: Security only, Type II, 12-month period* `[assumption]`.
   - **Controls and systems:** the controls list if one exists, or the tools they run on
     (identity provider, cloud, HR system, ticketing, code hosting, monitoring).

   Owners and system names come from the user. A missing owner is a gap to fill, not a
   name to guess.

2. **Draft controls where none exist.** If the user has no controls list, propose the
   minimum set for the categories in scope from [`reference.md`](reference.md), each
   written as *who does what, how often, with what record*:
   ✅ "Engineering managers review production access quarterly in Okta; removals are
   ticketed in Jira." ❌ "Access is managed appropriately." Mark proposed controls
   `proposed` so nobody mistakes them for existing ones.

3. **Map each control to criteria.** Use criteria IDs (for example CC6.2) only where
   [`reference.md`](reference.md) gives the ID; for anything else, name the area in words
   ("Privacy: notice to data subjects"). One control usually maps to one to three criteria.
   Then invert the map: every criterion in scope has at least one control, or it is a gap.

4. **Name the evidence for each control, by report type.**
   - **Type I** (point in time): show the control is designed and in place on the report
     date. The policy or procedure, the system configuration (export or screenshot with
     the date visible), and one example of it happening.
   - **Type II** (over the period): show it operated throughout. The auditor asks for the
     **complete population** of occurrences in the period from the system of record (all
     joiners, all leavers, all production changes, all quarterly reviews) and then picks
     samples; for each sample you produce the record. Name the population and its source.
   ✅ "Population: Workday termination report for the period. Per sample: Okta deactivation
   timestamp within 24 hours of the termination date." ❌ "Evidence: offboarding docs."

5. **Record where it lives, who owns it, and how often.** System is the tool the evidence
   is exported from, not the team. Owner is a person or a role a person holds. Frequency is
   how often the control runs (per event, daily, quarterly, annually) because that sets the
   sample size the auditor draws.

6. **Mark status and gaps honestly.** Each control is `in place`, `partial` (runs but leaves
   no record, or doesn't cover every system) or `gap` (doesn't exist or doesn't run). For
   Type II, a control that started mid-period is `partial` for this period. Every non-`in
   place` row gets a remediation and a date.

7. **Call out shared responsibility.** Controls a subservice organisation runs (the cloud
   provider's data centre security) are covered by its own SOC report: list the vendor
   reports to collect and the complementary controls the company must run itself. Note
   the controls the company expects its customers to run.

8. **Emit both outputs:**
   - the Markdown summary: scope line, a coverage table (criterion → controls → status),
     the evidence map table, the gap list ordered by audit risk, and the vendor SOC reports
     to collect;
   - the CSV in the columns of [`templates/evidence-map.csv`](templates/evidence-map.csv),
     one row per control-criterion pair, so the team can filter by owner or by criterion.

**Non-interactive runs** (subagent, CI, headless): missing scope becomes Security only,
Type II, 12 months, tagged `[assumption]` at the top. If there are no controls and no
description of the systems to draft from, emit
`BLOCKED: need the controls list, or the systems the company runs (identity, cloud, HR, ticketing, code hosting)`.

## Useful references in this skill

- [`reference.md`](reference.md): the Trust Services Criteria structure, the criteria IDs this skill uses, baseline controls per area, Type I vs Type II evidence, populations and sampling, and subservice organisations
- [`templates/evidence-map.csv`](templates/evidence-map.csv): the CSV columns with one annotated row
- [`examples/northwind-type2-security.md`](examples/northwind-type2-security.md): worked example, a fictional SaaS company preparing for its first Type II

## Quality bar

- **Every criterion in scope has a control or is listed as a gap.** The coverage table shows it.
- **Every control is written as who, what, how often, with what record.** No adjectives in place of a mechanism.
- **Evidence is specific to the report type:** Type I names design evidence; Type II names the population, its source system, and the per-sample record.
- **Criteria IDs appear only where reference.md gives them;** anything else is described in words.
- **System, owner and frequency are filled for every row,** or the blank is itself a gap.
- **Status is honest:** a control with no record, or one that started mid-period, is not `in place`.
- **Proposed controls are marked `proposed`,** never presented as existing.

## When to use this skill

- ✅ Getting ready for a first SOC 2 Type I or Type II audit, or a readiness assessment
- ✅ Turning a controls spreadsheet into an evidence request list per owner
- ✅ Moving from Type I to Type II and working out what has to be recorded over the period
- ✅ Adding a category (Availability, Confidentiality) to an existing SOC 2 scope

## When NOT to use this skill

- ❌ Finding security threats in a system design: use `threat-model`
- ❌ Scoring business risks for a risk committee: use `risk-register`; SOC 2's risk assessment criteria expect one, and this map can point to it
- ❌ A GDPR assessment of one processing activity: use `dpia`
- ❌ Writing the security or reliability targets for a service: use `nfr-spec`
- ❌ A policy for staff use of AI tools: use `ai-usage-policy`

## Anti-patterns to avoid

- ❌ **Evidence named as a document type.** "Access review docs" tells the owner nothing. Name the export, the system and what each sample must show.
- ❌ **Type I evidence for a Type II audit.** One screenshot proves the setting existed on one day, not for twelve months.
- ❌ **Invented criteria numbers.** If you're not sure of the ID, describe the area; a wrong ID in an auditor-facing map costs credibility.
- ❌ **Owner "Engineering".** A team can't be chased for a missing export; name the role.
- ❌ **Policies as controls.** "We have an access control policy" is evidence of design, not a control that operates.
- ❌ **Ignoring the cloud provider.** Physical security and data centre controls are carved out to its SOC report; the map should say so and list the complementary controls.
- ❌ **Marking a mid-period control `in place`.** For Type II, the auditor tests the whole period; a control that began in month seven is a gap for months one to six.
