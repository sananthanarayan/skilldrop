# Example: on-site bike repair subscription

## Input

> Lean canvas for my idea please. SpokeStop: a mechanic with a folding repair stand visits
> office bike racks once a week, and members get unlimited tune-ups and puncture fixes for
> $12 a month. People who cycle to work hate losing an evening to the bike shop. Early
> adopters: daily cycle commuters at offices with 500+ staff in the business district — the
> council's travel survey says about 2,000 people cycle in daily. 12 people at my running
> club said they'd definitely sign up. Channels: Instagram ads, and a stall at the city
> cycling festival in June. Our test Instagram campaign cost $900 and got 10 paying sign-ups.
> Mechanic time and parts work out at $7 per member per month. Fixed costs are a van lease
> and insurance at $6,000 a month. Members will probably drop off in winter, so I'd guess
> six months average. Unfair advantage: my folding stand design, nobody else has one.

## Output

**Riskiest assumption: that commuters need repairs often enough to keep paying $12 every
month.** It scores 9 (likely wrong × fatal). The 10 Instagram sign-ups show people will try
it, not that they stay; the six-month lifetime is a guess; and the economics below lose money
on every member, so how often the problem bites is what decides the model. A better stand
changes none of that, which is why the solution isn't the risk here.

Test it this week: stand at two office bike racks for a morning each and ask 20 cyclists
about the last time their bike needed fixing; don't pitch. **Fail if fewer than 6 paid for a
repair in the past three months.** Cost: $0. Time: two mornings. If it fails, the offer moves
from a subscription to pay-per-fix.

**Change before building:**
- Each member costs $90 to acquire and returns $30 of margin over six months: every sign-up
  adds a $60 loss, so growth deepens it.
- Break-even needs 1,200 members at once, 60% of the 2,000 daily cyclists the survey counts.

**Canvas**

| Box | Entry | Tag |
|---|---|---|
| Problem | Losing an evening to the bike shop for routine repairs; how often it happens is unknown | `[assumption]` |
| Customer segments | Daily cycle commuters in the business district; early adopter: those at offices with 500+ staff | `[evidence: council survey, ~2,000 daily]` for the size; `[assumption]` that they feel the problem |
| UVP | Your bike fixed at the office rack while you work | `[assumption]` |
| Solution | Weekly mechanic visit with a folding stand; unlimited tune-ups and puncture fixes | `[evidence: founder's design]` |
| Channels | Instagram ads; stall at the June cycling festival | `[evidence: $900 test → 10 sign-ups]` for Instagram; festival `[assumption]` and reaches leisure riders, not only commuters |
| Revenue streams | $12 a month per member | `[evidence: stated price]` |
| Cost structure | $7 per member per month; $6,000 a month fixed; $90 to acquire a member | `[evidence: founder's figures]`; CAC derived as $900 ÷ 10 |
| Key metrics | `[not stated]` — paid members and months retained are the two that test the model | `[assumption]` |
| Unfair advantage | None yet. The folding stand is a feature any mechanic can buy or copy. A candidate: exclusive access agreements with office landlords, if they would sign them | — |

The running-club interest is from the wrong segment (runners, not cycle commuters) and is
stated intent, so the problem box stays an assumption.

**Next assumptions**

2. **Members stay six months** (score 6: likely wrong — a guess with winter churn named —
   × pivot). Test: a concierge month for the 10 Instagram sign-ups, then count who renews.
   Fail if fewer than 7 of 10 renew for month two. Cost: one mechanic day a week. Time: five
   weeks.
3. **Instagram reaches commuters at $10 or less per paying member** (score 6). $10 is a
   third of lifetime margin, the most a member can cost if the fixed costs are to be covered.
   Test: $200 on ads targeted to the business district. Fail above $10 per paying sign-up.
   Time: one week. Today's $90 is nine times over it.

**Unit economics** (computed)
- Contribution: $12 − $7 = $5 a member a month (41.7% gross margin)
- Lifetime margin: $5 × 6 = $30; LTV:CAC 0.33
- CAC payback: $90 ÷ $5 = 18 months, three times the six-month lifetime
- Break-even: $6,000 ÷ $5 = 1,200 active members
- Most a member can cost to acquire: $30 at break-even, $10 at 3:1

**To confirm:** how the six-month lifetime was arrived at; whether the 10 Instagram
sign-ups were commuters; whether office landlords allow a mechanic at the racks.

Next step: run the two rack mornings before ordering anything for the van.
