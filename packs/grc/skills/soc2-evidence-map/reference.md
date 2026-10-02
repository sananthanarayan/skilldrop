# soc2-evidence-map reference

A drafting aid for SOC 2 preparation, based on the AICPA's 2017 Trust Services Criteria
(TSC), as revised in 2022 (the revision updated points of focus, not the criteria
numbering). It is not audit advice; the service auditor decides what is sufficient. Confirm
wording against the AICPA publication the auditor is using.

## Structure

SOC 2 reports on up to five **Trust Services Categories**:

| Category | Always in scope? | Criteria |
|---|---|---|
| Security | yes | The **common criteria**, CC1 to CC9 |
| Availability | optional | A1 series |
| Confidentiality | optional | C1 series |
| Processing Integrity | optional | PI1 series |
| Privacy | optional | The privacy criteria series |

The common criteria apply to every report. CC1 to CC5 follow the 17 principles of the COSO
2013 internal control framework; CC6 to CC9 add criteria specific to technology and security.

## Criteria IDs this skill uses

Use only these IDs. For any other point, describe the area in words.

**CC1 Control environment**
- CC1.1 commitment to integrity and ethical values
- CC1.2 board independence and oversight of internal control
- CC1.3 structures, reporting lines, authorities and responsibilities
- CC1.4 commitment to attract, develop and retain competent people
- CC1.5 holding people accountable for their internal control responsibilities

**CC2 Communication and information**
- CC2.1 obtaining and using relevant, quality information
- CC2.2 internal communication of objectives and responsibilities
- CC2.3 communication with external parties

**CC3 Risk assessment**
- CC3.1 objectives specified clearly enough to identify risks
- CC3.2 identifying and analysing risks
- CC3.3 considering the potential for fraud
- CC3.4 identifying and assessing changes that could affect internal control

**CC4 Monitoring activities**
- CC4.1 ongoing and separate evaluations of controls
- CC4.2 evaluating and communicating deficiencies

**CC5 Control activities**
- CC5.1 selecting and developing control activities
- CC5.2 general control activities over technology
- CC5.3 deploying controls through policies and procedures

**CC6 Logical and physical access controls**
- CC6.1 logical access security over information assets
- CC6.2 registering and authorising users before issuing credentials, and removing them when access is no longer authorised
- CC6.3 authorising, modifying and removing access based on roles, least privilege and segregation of duties
- CC6.4 restricting physical access to facilities and protected assets
- CC6.5 discontinuing protections over physical assets only after data is removed (disposal)
- CC6.6 protecting against threats from outside the system boundary
- CC6.7 restricting the transmission, movement and removal of information
- CC6.8 preventing or detecting unauthorised or malicious software

**CC7 System operations**
- CC7.1 detecting configuration changes and new vulnerabilities
- CC7.2 monitoring system components for anomalies
- CC7.3 evaluating security events to decide whether they are incidents
- CC7.4 responding to identified security incidents
- CC7.5 recovering from identified security incidents

**CC8 Change management**
- CC8.1 authorising, designing, developing, configuring, documenting, testing, approving and implementing changes

**CC9 Risk mitigation**
- CC9.1 risk mitigation for business disruption
- CC9.2 assessing and managing risks from vendors and business partners

**A1 Availability**
- A1.1 managing capacity to meet objectives
- A1.2 environmental protections, software, data backup and recovery infrastructure
- A1.3 testing recovery plan procedures

**C1 Confidentiality**
- C1.1 identifying and maintaining confidential information
- C1.2 disposing of confidential information

**Processing Integrity** (describe by area): definitions of the data processed and the
service's specifications; complete and accurate inputs; complete, accurate and timely
processing; complete and accurate outputs; and storage of inputs, items in process and
outputs.

**Privacy** (describe by area): notice; choice and consent; collection; use, retention and
disposal; access by data subjects; disclosure and notification, including breaches;
quality; and monitoring and enforcement.

## Baseline controls by area

A starting set for Security when the company has no controls list. Every one is written as
who, what, how often, with what record. Mark them `proposed` until the company confirms.

| Area | Control | Usual criteria |
|---|---|---|
| Governance | Leadership approves security policies annually; staff acknowledge them at hire and annually | CC1.1, CC5.3 |
| People | Background checks before start; security training at hire and annually, completion tracked | CC1.4 |
| Risk | Annual risk assessment with a register, reviewed by leadership | CC3.2, CC3.4 |
| Vendors | Critical vendors assessed at onboarding and annually; their SOC reports reviewed | CC9.2 |
| Joiners | Access granted by ticket with manager approval, by role | CC6.2, CC6.3 |
| Leavers | Access removed within a stated time of termination, triggered from HR | CC6.2 |
| Access review | Quarterly review of production and admin access, with removals recorded | CC6.3 |
| Authentication | SSO with MFA enforced for all workforce accounts | CC6.1 |
| Encryption | Data encrypted at rest and in transit, configured centrally | CC6.1, CC6.7 |
| Endpoints | Managed devices with disk encryption and malware protection | CC6.8 |
| Vulnerabilities | Scans on a schedule; findings fixed within SLAs by severity | CC7.1 |
| Monitoring | Security alerts routed to an on-call rotation | CC7.2, CC7.3 |
| Incidents | Incident response plan, tested annually; incidents ticketed with post-incident review | CC7.3, CC7.4, CC7.5 |
| Change | Production changes through pull requests with peer review and passing tests; no self-approval | CC8.1 |
| Backups | Automated backups; restore tested at least annually | A1.2, A1.3 (if Availability in scope), CC7.5 |
| Business continuity | Continuity and disaster recovery plan, reviewed and tested annually | CC9.1, A1.3 |
| Monitoring of controls | Internal review of control operation, deficiencies tracked to closure | CC4.1, CC4.2 |

## Type I vs Type II evidence

| | Type I | Type II |
|---|---|---|
| What the auditor opines on | Whether controls are suitably designed and implemented **as of a date** | Whether controls are suitably designed **and operated effectively throughout a period** |
| Period | One date | A period agreed with the auditor; commonly 6 or 12 months, sometimes 3 for a first report |
| Typical evidence | Policy or procedure; configuration export or dated screenshot; one example of the control running | The **full population** of occurrences in the period from the system of record, then the record for each sample the auditor picks |
| What fails | No design, or not implemented on the date | Missed occurrences, late occurrences, or no record for a sample |

### Populations and sampling

For Type II, the auditor needs a complete, system-generated list of every time the control
should have run, so it can select samples and confirm none are missing.

| Control | Population | Source | Per-sample record |
|---|---|---|---|
| Leaver access removal | All terminations in the period | HR system report | Identity provider deactivation timestamp vs termination date |
| Joiner access | All new accounts in the period | Identity provider | Approved access ticket before the account was created |
| Change management | All production deployments in the period | CI/CD or code hosting | Pull request with an approver other than the author, and passing checks |
| Quarterly access review | The four quarterly reviews | Ticketing or GRC tool | Review sign-off, list reviewed, removals actioned |
| Vulnerability remediation | All high and critical findings in the period | Scanner | Fix date within the SLA, or an approved exception |

The control's **frequency** drives how many samples the auditor draws: a per-event or daily
control gets more samples than a quarterly one. The auditor sets the sample sizes.

## Subservice organisations and complementary controls

- A **subservice organisation** (a cloud provider, a payment processor) runs controls the
  company relies on. The report either **carves it out** (the usual approach: its controls
  are excluded and the company points to the vendor's own SOC report) or includes it.
- For carve-outs, the report lists **complementary subservice organisation controls**: what
  the company expects the vendor to do. Collect the vendor's current SOC 2 report and its
  bridge letter if the period doesn't line up.
- **Complementary user entity controls** are controls the company expects its customers to
  run, such as managing their own users' access in the product. List them so the system
  description can state them.
