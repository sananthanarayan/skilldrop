# dpia reference

This summarises the parts of the EU GDPR (Regulation (EU) 2016/679) and the EDPB-endorsed
guidance a DPIA draft relies on. The UK GDPR keeps the same structure for these articles.
Check the supervisory authority's own guidance and DPIA list for the country concerned; this
file is a drafting aid, not legal advice.

## What a DPIA must contain: Article 35(7)

The assessment contains at least:

| Part | What the regulation asks for | Where it goes in the template |
|---|---|---|
| (a) | A systematic description of the envisaged processing operations and the purposes of the processing, including, where applicable, the legitimate interest pursued by the controller | §2 Description of the processing |
| (b) | An assessment of the necessity and proportionality of the processing operations in relation to the purposes | §3 Necessity and proportionality |
| (c) | An assessment of the risks to the rights and freedoms of data subjects | §4 Risks to individuals |
| (d) | The measures envisaged to address the risks, including safeguards, security measures and mechanisms to ensure the protection of personal data and to demonstrate compliance, taking into account the rights and legitimate interests of data subjects and other persons concerned | §5 Measures and residual risk |

Other parts of Article 35 that shape the draft:

- **Art. 35(1):** a DPIA is required where processing, in particular using new technologies, is likely to result in a high risk to the rights and freedoms of natural persons. It is done before the processing starts. One assessment may cover a set of similar processing operations with similar high risks.
- **Art. 35(2):** the controller seeks the advice of the data protection officer, where one is designated.
- **Art. 35(3):** a DPIA is required in particular for (a) a systematic and extensive evaluation of personal aspects based on automated processing, including profiling, on which decisions are based that produce legal effects or similarly significantly affect the person; (b) processing on a large scale of special categories of data (Art. 9(1)) or of personal data relating to criminal convictions and offences (Art. 10); (c) systematic monitoring of a publicly accessible area on a large scale.
- **Art. 35(4):** each supervisory authority publishes a list of processing that requires a DPIA. Check it.
- **Art. 35(9):** where appropriate, the controller seeks the views of data subjects or their representatives (for employees: a works council or union) on the intended processing.
- **Art. 35(11):** the controller reviews the assessment, at least when the risk represented by the processing changes.

## Screening: the nine criteria

The Article 29 Working Party guidelines on DPIA (WP248 rev.01), endorsed by the EDPB, list
nine criteria. Processing that meets two or more will in most cases need a DPIA; one can be
enough.

1. Evaluation or scoring, including profiling and predicting
2. Automated decision-making with legal or similarly significant effect
3. Systematic monitoring
4. Sensitive data or data of a highly personal nature
5. Data processed on a large scale
6. Matching or combining datasets
7. Data concerning vulnerable data subjects (including employees, children, patients)
8. Innovative use or applying new technological or organisational solutions
9. Processing that prevents data subjects from exercising a right or using a service or a contract

## Lawful basis: Article 6(1)

Each purpose needs one of:

| Point | Basis | Watch for |
|---|---|---|
| (a) | Consent | Must be freely given, specific, informed and unambiguous, and as easy to withdraw as to give. EDPB guidance on consent says employees can rarely give it freely to their employer. |
| (b) | Contract | Only processing that is necessary to perform a contract with the person, or to take steps they asked for before entering one. |
| (c) | Legal obligation | Name the law that imposes the obligation. |
| (d) | Vital interests | Protecting someone's life; rarely the right basis for routine processing. |
| (e) | Public task | Public authorities and tasks in the public interest set out in law. |
| (f) | Legitimate interests | Needs a documented balancing test: the interest, why the processing is necessary for it, and why it doesn't override the person's interests and rights. Not available to public authorities performing their tasks. |

Employment processing may also be subject to national rules adopted under **Article 88**.

## Special category and criminal offence data

**Article 9(1)** special categories: racial or ethnic origin, political opinions, religious or
philosophical beliefs, trade union membership, genetic data, biometric data processed to
uniquely identify a person, data concerning health, and data concerning a person's sex life
or sexual orientation.

Processing them needs an Article 6 basis **and** an Article 9(2) condition, for example
explicit consent (9(2)(a)) or obligations in employment, social security and social
protection law (9(2)(b)), many of which depend on member state law. Name the condition, or
raise an open question for the DPO.

**Article 10:** personal data about criminal convictions and offences may be processed only
under official authority or where authorised by law. Flag it separately.

Watch for inferred special category data: sickness absence is health data; location near a
place of worship or a clinic can reveal more than intended.

## Transfers outside the EEA: Chapter V

For each recipient outside the EEA, record the country and the mechanism:

- **Adequacy decision** (Art. 45): the European Commission has decided the country gives adequate protection. For the US, the EU-US Data Privacy Framework adequacy decision (July 2023) covers only organisations certified under it; check the recipient's certification and the decision's current status.
- **Appropriate safeguards** (Art. 46): most often the Commission's standard contractual clauses, or binding corporate rules within a group. Supplement them with a transfer impact assessment where the destination's laws may undermine them.
- **Derogations** (Art. 49): narrow, for occasional transfers; not a basis for routine, systematic transfers.

Remote access from outside the EEA (a support team viewing data) counts as a transfer.

## Scoring risks to individuals

Score for the person, not the controller. Harms to consider (Recital 75 lists examples):
discrimination, identity theft or fraud, financial loss, damage to reputation, loss of
confidentiality, significant economic or social disadvantage, being deprived of rights and
freedoms, losing control over their personal data, and physical harm.

| | Severity: minimal | Severity: significant | Severity: severe |
|---|---|---|---|
| **Likelihood: probable** | medium | high | high |
| **Likelihood: possible** | low | medium | high |
| **Likelihood: remote** | low | low | medium |

- **Remote:** needs several things to go wrong, or has not happened in comparable processing.
- **Possible:** could happen with the current design in the normal course of things.
- **Probable:** expected to happen to some people, given the design.
- **Minimal:** inconvenience, quickly overcome.
- **Significant:** real consequences the person can overcome with some difficulty: lost income, distress, an unfair decision that is later reversed.
- **Severe:** consequences that are serious or hard to reverse: loss of a job, discrimination, financial hardship, harm to health or safety.

Use the organisation's own scale when it has one.

## Prior consultation: Article 36

- **Art. 36(1):** the controller consults the supervisory authority before processing where the DPIA indicates the processing would result in a high risk in the absence of measures taken by the controller to mitigate the risk. In practice: a residual risk that stays high after the measures.
- **Art. 36(2):** the authority gives written advice within eight weeks of the request, extendable by six weeks for complex processing.
- **Art. 36(3)** lists what to send, including the DPIA itself and the DPO's contact details.

## Roles

- The **controller** is responsible for the DPIA. A **processor** assists the controller with it under the Article 28 contract.
- The **DPO** advises and monitors performance of the DPIA; the DPO does not own the decision. Record the DPO's advice and, if the controller departs from it, why.
