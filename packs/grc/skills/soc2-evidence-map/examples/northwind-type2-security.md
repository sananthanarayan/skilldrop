# Worked example: Northwind Analytics, first SOC 2 Type II (Security)

A fictional 60-person SaaS company. The input is what its Head of Security might send; the
output is the summary and the CSV, shortened where rows repeat a pattern.

## Input given to the skill

> We're Northwind Analytics. A big customer wants a SOC 2 Type II, Security only, and our
> auditor has proposed a six-month period, 1 January to 30 June 2027. We don't have a formal
> controls list. What we do today:
> - Okta SSO with MFA for everyone. Access is requested by Jira ticket with manager approval
>   and granted through role-based Okta groups (Dev Rao, IT Lead).
> - BambooHR terminations deactivate Okta automatically, within the day.
> - Background checks through Certn before start, KnowBe4 training within 30 days (Ola
>   Brandt, People Ops).
> - Laptops in Kandji with FileVault and malware protection. Four contractors use their own
>   laptops.
> - Snyk scans weekly; criticals fixed in 14 days, highs in 30 (Rui Costa, Platform Lead).
> - Datadog security alerts page the PagerDuty on-call.
> - All deploys go through GitHub PRs with one approval and CI, but two admins can bypass
>   branch protection (Kim Novak, VP Engineering).
> - RDS daily backups. Never tested a restore.
> - We wrote security policies in 2025, CEO approved them. Nobody has acknowledged them.
> - Incident response plan exists, never tested. We have a vendor list in Vanta.
> - Engineering managers "look at" AWS and GitHub admin access now and then.
> - We're on AWS; no production data in the office.
> I'm Sam Ito, Head of Security.

No question was needed: scope, type, period, systems and most owners were given.

---

## Scope

SOC 2 Type II, Security (common criteria CC1–CC9), Northwind Analytics production platform,
period 1 January 2027 to 30 June 2027. AWS is treated as a carved-out subservice
organisation `[assumption: confirm with the auditor]`.

> Prepared for Northwind's compliance lead and auditor to review; not audit advice. The
> auditor decides what evidence is sufficient.

## Coverage by criterion

| Criteria | Controls | Status |
|---|---|---|
| CC1.1, CC5.3 | GOV-01 policy approval and acknowledgement | partial |
| CC1.4 | HR-01 background checks and training | in place |
| CC1.2, CC1.3, CC1.5 | none | **gap**: GOV-02, GOV-03 proposed |
| CC2.1, CC2.2, CC2.3 | none (GOV-01 covers part of CC2.2) | **gap**: COM-01 proposed |
| CC3.1–CC3.4, CC5.1 | RISK-01 risk assessment | **gap**: RISK-01 not yet run |
| CC4.1, CC4.2 | none | **gap**: MON-02 proposed |
| CC5.2 | none mapped yet | **gap**: map once technology controls are confirmed |
| CC6.1 | AC-04 SSO with MFA | in place |
| CC6.2 | AC-01 joiners, AC-02 leavers | in place |
| CC6.3 | AC-01 role groups; AC-03 access review | partial (AC-03 is a gap) |
| CC6.4 | AWS (carved out); office holds no production data | subservice `[to confirm]` |
| CC6.5, CC6.6, CC6.7 | none | **gap**: EP-02, NET-01, ENC-01 proposed |
| CC6.8 | EP-01 managed laptops | partial |
| CC7.1 | VM-01 vulnerability scanning | in place |
| CC7.2 | MON-01 alert routing | in place |
| CC7.3, CC7.4 | IR-01 incident response | partial |
| CC7.5 | IR-01; BC-01 restore tests | partial |
| CC8.1 | CHG-01 pull request review | partial |
| CC9.1 | none | **gap**: BC-02 proposed |
| CC9.2 | VEN-01 vendor reviews | partial |

## Evidence map (selected rows; full set in the CSV)

| Control | Criteria | Type II population (source) | Per-sample record | System | Owner | Frequency | Status |
|---|---|---|---|---|---|---|---|
| AC-02 IT removes all access within 24 hours of termination, triggered from BambooHR | CC6.2 | All terminations in the period (BambooHR report) | Okta deactivation timestamp within 24 hours of termination date | BambooHR; Okta | IT Lead (Dev Rao) | per event | in place |
| AC-03 Engineering managers review AWS and GitHub admin access quarterly; removals ticketed | CC6.3 | The two quarterly reviews in the period (Jira) | Signed-off access list and a ticket per removal | Jira; AWS IAM Identity Center; GitHub | VP Engineering (Kim Novak) | quarterly | **gap** |
| CHG-01 Production deploys only via PR with a non-author approval and passing CI | CC8.1 | All production deployments (GitHub Actions) | PR with non-author approval and green checks | GitHub | VP Engineering (Kim Novak) | per event | partial |
| EP-01 All laptops managed in Kandji with encryption and malware protection | CC6.8 | Device compliance reports for the period | Sampled devices encrypted and protected | Kandji | IT Lead (Dev Rao) `[to confirm]` | continuous | partial |
| BC-01 Daily RDS backups; restore tested every six months | CC7.5 | Restore tests in the period (Jira) | Restore record with date and outcome | AWS RDS; Jira | Platform Lead (Rui Costa) `[to confirm]` | semi-annually | proposed |

For a **Type I** on the same scope, the CHG-01 evidence would be the branch protection
settings export dated on the report date plus one merged PR, with no population. Here the
auditor will sample deployments from all six months, so the bypass rights matter for every
day of the period.

## Gaps, ordered by audit risk

1. **CHG-01 branch protection bypass** (CC8.1). Every bypassed deploy is an exception the
   auditor finds by sampling. Remove bypass rights, or log and review each bypass, before
   1 January. *Owner: Kim Novak. Due 2026-11-15.*
2. **AC-03 no access review record** (CC6.3). Schedule a quarterly review ticket and run the
   first before the period starts so Q1 and Q2 both have evidence. *Owner: Kim Novak. Due 2026-12-15.*
3. **RISK-01 no risk assessment** (CC3.1–CC3.4). Run one in January and minute leadership's
   review. *Owner: Sam Ito. Due 2027-01-31.*
4. **GOV-01 no acknowledgements** (CC1.1). Run the acknowledgement cycle in December so every
   person in the population has a date. *Owner: Sam Ito. Due 2026-12-15.*
5. **EP-01 four unmanaged contractor laptops** (CC6.8). Enrol or replace. *Owner: Dev Rao `[to confirm]`. Due 2026-11-30.*
6. **IR-01 untested plan, BC-01 untested restore** (CC7.4, CC7.5). Each needs one recorded
   test inside the period. *Owners: Sam Ito, Rui Costa `[to confirm]`.*
7. **No control yet** for CC1.2, CC1.3, CC1.5, CC2.x, CC4.x, CC5.2, CC6.5–CC6.7 and CC9.1.
   Proposed controls are listed below; each needs an owner from Sam Ito.

Proposed controls (`proposed` until Northwind confirms):
- GOV-02: leadership reviews security posture and open risks quarterly, minuted (CC1.2).
- GOV-03: security roles and responsibilities documented in the org chart and job descriptions; policy breaches handled under the disciplinary policy (CC1.3, CC1.5).
- COM-01: security commitments published to customers and in contracts; internal security updates sent quarterly (CC2.1–CC2.3).
- MON-02: Head of Security reviews control operation quarterly and tracks deficiencies to closure (CC4.1, CC4.2).
- EP-02: laptops wiped and recorded before disposal or reassignment (CC6.5).
- NET-01: AWS security groups and WAF rules managed in code and reviewed on change (CC6.6).
- ENC-01: TLS enforced on all external endpoints; data at rest encrypted with KMS (CC6.7, CC6.1).
- BC-02: business continuity plan reviewed annually and tested by tabletop (CC9.1).

## Vendor SOC reports to collect

- AWS SOC 2 Type II covering the period, plus a bridge letter if it ends before 30 June 2027.
- Okta SOC 2 Type II.
- Complementary user entity controls to state in the system description: customers manage
  their own users' access and roles in Northwind's product `[to confirm]`.

## CSV

[`northwind-evidence-map.csv`](northwind-evidence-map.csv): 16 rows, one per
control-criterion pair, in the columns of the template.

---

**Why this is a passing output:** every common criterion is either covered or listed as a
gap; evidence names the population and source system for Type II; IDs used are only those in
the reference; owners are the people the user named, owners the skill inferred are marked
`[to confirm]`, and proposed controls are left for Sam to assign; the mid-period and untested controls are not marked `in place`; and AWS
is handled as a carve-out with the reports to collect.
