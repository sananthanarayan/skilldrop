# Worked example: Acme Logistics warehouse performance analytics

A fictional company. The input is what a business owner might send; the output is the DPIA
draft, shortened where sections repeat the same pattern.

## Input given to the skill

> We're rolling out "PickPulse" at our two Dutch warehouses (about 600 staff, including
> agency workers). It takes the handheld scanner data — every scan, timestamp, location in
> the aisle, idle time — and gives each picker a daily productivity score against a target.
> Team leads see a ranked list, and anyone under 85% of target for two weeks gets flagged
> for a performance conversation. It also uses the absence calendar to adjust targets for
> people coming back from sick leave. The vendor is US-based, hosted on AWS in Frankfurt,
> but their support team in the US can access the data. We'd keep the scan data for two
> years. Can you write the DPIA? Our DPO is Marieke de Vries.

The skill asked one question, "Does a flag lead straight to a warning or other sanction, or
does a team lead always review it first?", and the user answered: "A team lead reviews, but
in practice they mostly follow the flag."

---

# DPIA: Picker productivity scoring with PickPulse

> Draft prepared for review by the DPO. It is not legal advice; the controller decides.
> Items marked `[to confirm: …]` are unverified and repeated in §7.

| | |
|---|---|
| Controller | Acme Logistics B.V. `[to confirm: legal entity]` |
| Processing activity | Daily productivity scoring and flagging of warehouse pickers from scanner data |
| Business owner | `[to confirm: name, role]` |
| DPO | Marieke de Vries |
| Version / date | 0.1 draft / 2026-10-01 |
| Status | Draft for DPO advice |

## 1. Screening

| Criterion | Applies? | Why |
|---|---|---|
| Evaluation or scoring | yes | A daily productivity score per picker |
| Automated decision-making with legal or similar effect | possibly | Flags drive performance conversations; team leads "mostly follow the flag", so human review may not be meaningful |
| Systematic monitoring | yes | Every scan, location and idle period, all shift |
| Sensitive or highly personal data | yes | Sick-leave data used to adjust targets is health data |
| Large scale | possibly | About 600 people, continuous collection |
| Matching or combining datasets | yes | Scanner data combined with the absence calendar |
| Vulnerable data subjects | yes | Employees and agency workers, in an imbalance of power with the employer |
| Innovative technology | no | Productivity analytics is established |
| Prevents exercising a right or using a service | no | |

**Conclusion:** DPIA required. At least five criteria apply. The Dutch supervisory
authority's list `[to confirm: checked by DPO]` is also likely to cover employee monitoring.

## 2. Description of the processing (Art. 35(7)(a))

**What happens:** scanners record each scan → PickPulse ingests events every 15 minutes →
scores computed nightly against targets, adjusted for return from sick leave → team leads
see a ranked list → pickers under 85% for two weeks are flagged → team lead holds a
performance conversation → scan data deleted after two years.

**Purposes:**

| # | Purpose | Lawful basis (Art. 6(1)) | Art. 9(2) condition | Notes |
|---|---|---|---|---|
| P1 | Measuring warehouse throughput to plan staffing | (f) legitimate interests | n/a | Achievable with team-level, not individual, data |
| P2 | Individual productivity scoring and flagging | (f) legitimate interests `[to confirm: balancing test]` | n/a | Consent would not be freely given by employees |
| P3 | Adjusting targets after sick leave | `[to confirm]` | `[to confirm: none identified]` | Health data; see Q3 |

Legitimate interest pursued (P1, P2): running the warehouses efficiently and managing
performance fairly.

**Data inventory:**

| Data category | Special category? | Data subjects | Source | Recipients and processors | Location / transfer | Retention |
|---|---|---|---|---|---|---|
| Employee ID, name, team, shift | no | Pickers (employees and agency workers) | HR system | Team leads; PickPulse vendor (processor) | EU (AWS Frankfurt); US support access | `[to confirm]` |
| Scan events: item, timestamp, aisle location | no | Pickers | Handheld scanners | PickPulse vendor | As above | 2 years (stated) |
| Idle time between scans | no | Pickers | Derived | Team leads; vendor | As above | 2 years (stated) |
| Productivity score, rank, flag | no | Pickers | Derived | Team leads; HR on escalation | As above | `[to confirm]` |
| Return-from-sick-leave dates | **yes, health** | Pickers | Absence calendar | PickPulse vendor | As above | `[to confirm]` |

**Transfers:** US vendor support staff can access the data, which is a transfer to the US.
Mechanism `[to confirm: vendor certified under the EU-US Data Privacy Framework, or SCCs
with a transfer impact assessment]`. Agency workers' data may also be shared back with the
agency `[to confirm]`.

## 3. Necessity and proportionality (Art. 35(7)(b))

| Question | Answer |
|---|---|
| Is each purpose necessary? | P1 yes, but team-level aggregates would meet it. P2 is the intrusive purpose; its necessity rests on the balancing test. |
| Less intrusive alternative? | Aisle-level location and idle time are more detail than a daily score needs. Scoring on completed picks per hour, without location, would meet P2. |
| Retention justified? | Two years of event-level scan data has no stated reason. The score could be kept; raw events could be aggregated after 30 days `[proposed]`. |
| How are people told? | No notice described `[to confirm]`. |
| Rights | No route described for a picker to see or contest their score `[to confirm]`. |
| Decisions without human review (Art. 22)? | At risk. Team leads "mostly follow the flag"; if review is a rubber stamp, the flag is in effect an automated decision with a significant effect. |
| Processor contract (Art. 28)? | `[to confirm]` |
| Works council consulted (Art. 35(9))? | `[to confirm]`. In the Netherlands, works council involvement is also likely to be required under employment law; see Q6. |

## 4. Risks to individuals (Art. 35(7)(c))

| # | Risk to the person | Likelihood | Severity | Inherent |
|---|---|---|---|---|
| R1 | Pickers with a disability, a health condition or pregnancy are scored as low performers and face disciplinary steps for reasons unrelated to effort | probable | severe | **high** |
| R2 | Flags are followed without real review, so pickers face performance action from an automated score they can't see or challenge | probable | significant | **high** |
| R3 | Return-from-sick-leave data reveals health information to team leads and the vendor beyond what is needed | possible | significant | medium |
| R4 | Continuous location and idle-time tracking creates pressure to skip breaks or toilet visits, harming health | possible | severe | **high** |
| R5 | US support access exposes data to authorities without equivalent safeguards | remote | significant | low |
| R6 | Two years of event-level data is reused for other purposes (for example, investigations) without people knowing | possible | significant | medium |

## 5. Measures and residual risk (Art. 35(7)(d))

| Risk | Measure | Owner | Status | Residual |
|---|---|---|---|---|
| R1 | Exclude time with an agreed adjustment from scoring; let pickers record reasonable adjustments with HR, not team leads | HR | proposed | high (unchanged until agreed) |
| R2 | A flag starts a review only; the team lead must record a reason before any action; pickers see their own score and can contest it | Operations | proposed | high (unchanged until agreed) |
| R3 | Send PickPulse a "target adjustment" flag with an end date, not sick-leave dates | HR / vendor | proposed | medium |
| R4 | Remove idle-time and aisle-location from individual views; exclude breaks from scoring | Operations | proposed | high (unchanged until agreed) |
| R5 | Confirm DPF certification or SCCs; restrict support access to on-request, logged sessions | Procurement | proposed | low |
| R6 | Aggregate scan events after 30 days; purpose limitation in the notice and the vendor contract | DPO / vendor | proposed | medium |

No measure is yet agreed, so residual risk equals inherent risk until the business commits.

## 6. Prior consultation (Art. 36)

R1, R2 and R4 are high with no agreed measures. **View: if those measures are not adopted,
prior consultation with the supervisory authority looks needed.** If the measures for R1,
R2 and R4 are agreed and bring each to medium or below, it does not look needed. For the
DPO to confirm.

## 7. Open questions for the DPO and the business

| # | Question | Who can answer | Blocks |
|---|---|---|---|
| Q1 | Has the legitimate interests balancing test for P2 been documented? | DPO with Operations | §2 P2 |
| Q2 | Is individual scoring needed at all, or would team-level throughput (P1) meet the business need? | Operations director | §3, R1, R2 |
| Q3 | What Art. 9(2) condition, if any, covers using sick-leave data to adjust targets, or can P3 work without health data (R3 measure)? | DPO | §2 P3 |
| Q4 | Is the vendor certified under the EU-US Data Privacy Framework, or are SCCs in place? | Procurement / vendor | §2 transfers |
| Q5 | What are the retention periods for scores, flags and the employee profile? | HR / Operations | §2 inventory |
| Q6 | Has the works council been consulted, and is its consent required? | HR / employment counsel | §3 |
| Q7 | Is agency workers' data shared with the agencies, and on what basis? | HR | §2 inventory |

## 8. DPO advice and sign-off

| | |
|---|---|
| DPO advice | |
| Advice followed? If not, why | |
| Residual risks accepted by | |
| Decision | |
| Next review date or trigger | |

---

**Why this is a passing output:** risks are harms to pickers, not to Acme; each purpose has
its own basis; health data is called out and lacks a condition, so it becomes Q3 instead of
a guess; the US support access is treated as a transfer with the mechanism left to confirm;
retention the user didn't give is `[to confirm]`; residual risk doesn't drop on proposed
measures; and the sign-off block is blank.
