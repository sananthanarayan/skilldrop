---
name: dpia
description: Draft a data protection impact assessment (DPIA) for one processing activity in the structure GDPR Article 35(7) requires — a systematic description of the processing and its purposes, necessity and proportionality, risks to the rights and freedoms of individuals, and the measures to address them — with a data inventory (categories, special category data, data subjects, sources, recipients, transfers outside the EEA, retention), the lawful basis per purpose, a likelihood × severity risk table scored for harm to people, residual risk, a view on prior consultation, and the open questions for the DPO. Use when the user needs a DPIA or PIA, is launching something that processes personal data in a new or risky way, or asks "do we need a DPIA", "write the DPIA for…", "privacy impact assessment".
---

# dpia

You draft the DPIA a data protection officer can review, challenge and sign: one processing
activity, described precisely enough that a regulator could follow what happens to the data,
with risks scored for **the people the data is about**, not for the company. The output is
a Markdown document in the order GDPR Article 35(7) sets out, plus the questions only the
DPO or the business can answer. You prepare material for a qualified person (the DPO or
privacy counsel) to review; it is not legal advice, and the controller owns the decision.

## How to respond

1. **Ask once for what is missing, in one message.** Take what is already given. Ask for at
   most two things, and say what you will assume for the rest:
   - **The processing activity:** what happens, to whose data, for what purpose, using which
     systems and vendors. One activity per DPIA; split "the new HR platform" into its
     purposes if they differ (payroll, performance, monitoring).
   - **The facts you can't infer:** where vendors process data, retention periods, and
     whether any decision about a person is made without human review.

   Everything else you can't confirm goes in the draft as `[to confirm: …]` and in the DPO
   questions. Never fill a retention period, a vendor location or a lawful basis decision
   with a plausible guess and present it as fact.

2. **Screen first: say whether a DPIA looks required, and why.** Check the activity against
   the Article 35(3) cases and the nine criteria in the EDPB-endorsed guidelines (in
   [`reference.md`](reference.md)). Name each criterion that applies. Two or more usually
   means a DPIA is needed; also check the supervisory authority's own list. If none apply,
   say so and offer a short screening record instead of a full DPIA.

3. **Describe the processing systematically** (Art. 35(7)(a)). Build the data inventory
   from [`templates/dpia.md`](templates/dpia.md): data categories, special category data
   (Art. 9(1)) and criminal offence data called out separately, data subjects, sources,
   recipients and processors, transfers outside the EEA with the transfer mechanism,
   retention per category, and the data flow from collection to deletion. Include the
   legitimate interest pursued where that is the basis.

4. **Give a lawful basis per purpose,** not one for the whole activity. Each purpose gets one
   Article 6(1) basis; special category data also needs an Article 9(2) condition. Flag
   these as problems, not facts:
   ✅ "Purpose: shift allocation. Basis: legitimate interests [to confirm: balancing test]."
   ❌ "Lawful basis: consent." for employees, where the power imbalance makes consent hard
   to rely on; ❌ "Basis: GDPR compliance" (not a basis).

5. **Assess necessity and proportionality** (Art. 35(7)(b)). For each purpose: is the
   processing needed, could less data or a less intrusive method achieve it, how long is
   each category kept and why, how are people told (Arts. 13/14), and how do they exercise
   their rights. Say plainly where the design collects more than the purpose needs.

6. **Score the risks to individuals** (Art. 35(7)(c)). Each risk names the harm to a person:
   discrimination, financial loss, loss of confidentiality, loss of control over their data,
   being unable to exercise a right, physical harm, distress. Score likelihood (remote,
   possible, probable) × severity (minimal, significant, severe) = low, medium or high, using
   the matrix in [`reference.md`](reference.md).
   ✅ "Warehouse staff with a disability are ranked as low performers and face disciplinary
   review." ❌ "Reputational damage to Acme." ❌ "Regulatory fine." (company risks belong in
   `risk-register`).

7. **List measures against each risk** (Art. 35(7)(d)): what changes the design, who owns
   it, and whether it is in place or planned. Then rescore as **residual** risk, counting
   only measures the business has agreed to.

8. **Give a view on prior consultation.** If any residual risk stays high, say that prior
   consultation with the supervisory authority under Article 36 looks needed and why. If
   none does, say so. This is a view for the DPO, not a decision.

9. **End with the DPO questions and sign-off block.** Number the open questions; each names
   who can answer it. Leave the DPO advice, the decision and the sign-off fields blank.

10. **Emit the document** in the order of [`templates/dpia.md`](templates/dpia.md), with the
    not-legal-advice line once, at the top.

**Non-interactive runs** (subagent, CI, headless): unconfirmed details (retention, vendor
locations, the balancing test) become `[to confirm: …]` entries and DPO questions. If the
processing activity itself is not described (no data, no purpose), emit
`BLOCKED: need the processing activity: what personal data, whose, for what purpose, and which systems or vendors`.

## Useful references in this skill

- [`reference.md`](reference.md): what Article 35(7) requires, the screening criteria, lawful bases and special category conditions, transfer mechanisms, the risk matrix, and prior consultation
- [`templates/dpia.md`](templates/dpia.md): the DPIA skeleton, section by section
- [`examples/acme-warehouse-performance.md`](examples/acme-warehouse-performance.md): worked example, a warehouse productivity analytics tool for a fictional company

## Quality bar

- **The four Article 35(7) parts are all present,** in order: description and purposes, necessity and proportionality, risks to individuals, measures.
- **Risks are harms to people,** scored for likelihood and severity to them. No company-impact rows.
- **Every purpose has its own lawful basis,** and special category data has an Article 9(2) condition or an open question saying it lacks one.
- **Transfers outside the EEA name the destination and the mechanism,** or are marked `[to confirm]`.
- **Every unknown is visible:** `[to confirm]` in the body and a numbered DPO question, never a guess written as fact.
- **Residual risk counts only agreed measures,** and the prior consultation view follows from it.
- **Article numbers cited are ones the regulation actually contains** for that point; when unsure, describe the requirement without a number.

## When to use this skill

- ✅ A new product feature, system or vendor that processes personal data in a new way
- ✅ Employee monitoring, profiling, scoring, location tracking, or automated decisions about people
- ✅ Large-scale processing of health, biometric or other special category data
- ✅ Screening "do we need a DPIA for this?" before a project starts
- ✅ Refreshing an old DPIA after the processing changed

## When NOT to use this skill

- ❌ Security threats against a system design: use `threat-model`, and feed its findings into the measures section here
- ❌ Threats to an AI agent's tools and prompts: use `agent-threat-model`
- ❌ Rules for staff using AI tools: use `ai-usage-policy`
- ❌ Business risks to the company, scored for the company: use `risk-register`
- ❌ Mapping controls to SOC 2 audit evidence: use `soc2-evidence-map`

## Anti-patterns to avoid

- ❌ **Scoring risk to the company.** "Fine of up to 4% of turnover" is not a DPIA risk. The question is what happens to the person.
- ❌ **One lawful basis for everything.** Payroll, performance scoring and marketing are different purposes with different bases.
- ❌ **Consent from employees by default.** Use it only where refusing has no consequence for the person.
- ❌ **"Data is encrypted" as the only measure.** Encryption doesn't address unfair scoring, excessive retention or lack of transparency.
- ❌ **"Retention: as long as necessary."** Give a period per category, or mark it `[to confirm]`.
- ❌ **Invented article numbers.** A wrong citation in a DPIA costs the DPO's trust in the whole document.
- ❌ **Filling the DPO's sign-off.** The draft leaves advice, decision and signature blank.
- ❌ **The whole platform in one DPIA.** Assess one processing activity; list the others as separate DPIAs to do.
