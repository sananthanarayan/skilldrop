# SLOs — {service}

**{One to three lines: the decisions and anything that blocks them — an unreachable target, an
SLI measured in the wrong place, a journey too quiet to page on.}**

Assumptions: {window, traffic basis, anything tagged [assumption]}

## SLOs

| Journey | SLI (good / valid) | Measured at | Target / window | Budget |
|---|---|---|---|---|
| {journey} | Good: {…} / Valid: {… excluding …} | {LB / client / probe} | {99.x% / 30 d} | {N min · N bad requests at N/day} |

{Per journey, only where it changes something: why this target (history, dependency
ceiling), and what the measurement point still misses.}

## Alerts

| Journey | Burn | Long / short | Trips at | Budget at fire | Exhausts in | Action |
|---|---|---|---|---|---|---|
| {journey} | 14.4× | 1 h / 5 m | {x%} | {2%} | {50 h} | page |

{Low-traffic journeys: the expected bad-event count and the method used instead.}

## Error-budget policy

| Budget state | What changes | Owner |
|---|---|---|
| {state} | {action} | {role or name from the input} |

Exception route: {who approves, in writing, recorded where}. Exempt: {…}. Review: {when}.

## To confirm

- {each assumption or missing input, once}
