# risk-register reference

## The default 5×5 scale

Likelihood is judged over a stated horizon (default 12 months). Impact is judged against the
objective in scope, not against the company in general.

| Score | Likelihood | Rough probability | Impact | What it looks like |
|---|---|---|---|---|
| 1 | Rare | under 5% | Minimal | Absorbed in normal operations; nobody outside the team notices |
| 2 | Unlikely | 5–20% | Minor | Small cost or delay inside existing tolerance; no external notice |
| 3 | Possible | 20–50% | Moderate | A milestone or budget line is missed; management attention needed |
| 4 | Likely | 50–80% | Major | An objective is missed; customers, partners or a regulator notice |
| 5 | Almost certain | over 80% | Severe | The objective fails, serious legal or regulatory action, or harm to people |

Add the organisation's own thresholds to the impact column when it has them, for example
"Major: £250k to £1m, or one to three months' delay". Use the organisation's scale whenever
it exists; a register that uses a different scale from the risk committee gets rescored.

**Bands** (score = likelihood × impact): low 1–4, medium 5–9, high 10–16, critical 20–25.
The script bands other scales by share of the maximum score: up to 16% low, up to 36%
medium, up to 64% high, above that critical. On 5×5 that gives exactly the bands above.

A common use of the bands, to adapt to the organisation's appetite:

| Band | Who can accept the residual risk | Review at least |
|---|---|---|
| critical | Executive or board | monthly |
| high | Senior leader above the owner | quarterly |
| medium | Risk owner | six-monthly |
| low | Risk owner | yearly |

## Writing cause, event, consequence

| Part | Question it answers | ✅ | ❌ |
|---|---|---|---|
| Cause | What condition exists today? | "One analyst maintains the route scripts" | "Key person" |
| Event | What uncertain thing might happen? | "The analyst leaves or is off long-term" | "Resource issues" |
| Consequence | What happens to the objective? | "Routes are planned by hand and fuel use rises" | "Bad" |

Tests:
- If the "risk" is already happening, it is an **issue**, not a risk. Track it as an issue
  with an action, and keep the risk only if it could get worse.
- If you can't say how likely it is, the event is too vague. Rewrite it.
- If two causes lead to one event, keep one row and list both causes. If one cause leads to
  two unrelated events, write two rows.

## Inherent and residual

- **Inherent:** the score if none of the risk's controls existed. Use it to see which
  controls matter most; a big drop from inherent to residual means a control the business
  depends on, and that control deserves testing.
- **Residual:** the score with the controls that operate today. Controls that are planned,
  budgeted or half-built go in `controls` marked "(planned)" and do not lower residual yet.
- **Target** (optional, in the summary): where residual should land once planned controls are live.

## Treatments

| Treatment | Use when | Record |
|---|---|---|
| avoid | The activity isn't worth the risk | What stops, and by when |
| reduce | Controls can bring likelihood or impact down at a sensible cost | Each control, owner, due date |
| transfer | Someone else can carry the consequence: insurance, contract, outsourcing | The policy or clause; note the residual you still hold |
| accept | Treatment costs more than the exposure, and the residual is within appetite | Who accepted, when, and until what date |

Accepting a high or critical residual risk is a decision above the owner's level; put it in
the summary's decision list.

## Review triggers

Name an observable event, not a calendar entry:

- ✅ "Vendor misses an SLA two months running or announces a sale"
- ✅ "Diesel index up 10% in a month"
- ✅ "Any EDR detection on a depot device"
- ❌ "Quarterly review"
- ❌ "If things change"

The calendar date goes in `next_review`; the trigger is what brings the review forward.

## CSV columns

| Column | Required | Values |
|---|---|---|
| id | yes | unique, e.g. R-001 |
| title | yes | short noun phrase |
| cause, event, consequence | yes | one sentence each |
| owner | yes | a named person or a role a person holds; not "TBD", "IT", "team" |
| inherent_likelihood, inherent_impact | yes | whole numbers 1..scale |
| residual_likelihood, residual_impact | yes | whole numbers 1..scale; residual score ≤ inherent score |
| treatment | yes | avoid, reduce, transfer, accept |
| controls | no (warned under reduce) | semicolon-separated |
| due_date | no (warned under avoid, reduce, transfer) | YYYY-MM-DD |
| next_review | yes | YYYY-MM-DD |
| review_trigger | no (warned) | the event that reopens the risk |
| status | yes | open, closed |

Extra columns (category, objective, last_updated, target score) are allowed; the script
ignores them.
