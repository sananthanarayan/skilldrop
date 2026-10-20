---
name: lean-canvas
description: Turn a startup or internal-product idea into a lean canvas that finds what could kill it — the nine boxes filled only from what the user said, each entry tagged evidence-backed (with its source) or assumption, the assumptions ranked by how likely each is wrong times how badly the idea fails if it is, the cheapest test with a pass/fail line set in advance for the top ones, a computed unit-economics check when price and costs are given, and a plain call when the idea should change before anything is built. Use when the user says "lean canvas", "help me think through my startup idea", "what are the riskiest assumptions", "how do I validate this idea", "is this idea worth building", or "poke holes in my business model".
---

# lean-canvas

The canvas is the vehicle; the product is the assumption work. A filled-in grid tells the
founder what they already believe. This skill tells them which belief is most likely to sink
the idea, and the cheapest way to find out this week. For a costed invest/defer decision with
NPV and options, use `business-case`; for the press release and FAQ of an idea already
approved, `prfaq`; for market and competitor frameworks, `strategy-analysis`; for measuring a
feature after it ships, `success-metrics`.

## How to respond

**Four rules come before the steps and outrank them:**

- **Answer what was asked, first.** Open with the answer, the decision or the artifact, in plain words. Scores, matrices, frameworks and tags come after it, and anything that doesn't change the answer is cut.
- **Use only what you were given.** Don't add facts, names, numbers, incidents, history, steps or sections the input doesn't contain. What you need and don't have is left out of the artifact and listed once at the end under "To confirm".
- **Deliver from what you have.** When the request gives you something to work on, state your assumptions in a line and produce the result. When it gives you nothing to work on, ask for it in one or two plain sentences and say what you will do once you have it.
- **Write for someone who has never heard of this skill.** No skill names, no paths or scripts from this folder, no internal terms, and nothing about how the run was set up. A next step is one plain sentence at the end that describes the work.
- **For this skill:** A box with nothing behind it says so. "Unfair advantage: none yet" is a correct entry; an invented moat, channel or metric is a wrong one.

1. **Fill the nine boxes from the input only.** Problem (top 1–3), customer segments with the
   **early adopter** named separately, unique value proposition, solution, channels, revenue
   streams, cost structure, key metrics, unfair advantage. Tag every entry `[evidence: <source
   the user gave>]` or `[assumption]`. A box the user left empty gets `[not stated]`, not a
   filler. Internal products: revenue becomes the budget or saving that funds it, and the
   customer is the team that has to adopt it.

2. **Grade the evidence before trusting it.** Evidence counts for a box only when it comes
   from the stated early adopter and records behaviour, not opinion.
   - ✅ *"7 of the 20 cycle commuters we stopped at the office rack paid for a repair in the last three months"* — behaviour, right segment.
   - ❌ *"12 people from my running club said they'd definitely sign up"* — wrong segment (runners, not cycle commuters) and stated intent. Tag it `[evidence: running-club chat — wrong segment, intent only]` and rate the box as an assumption.
   - A third-party statistic (*"a council survey says 2,000 people cycle to the business district"*) sizes the segment; it doesn't show they feel the problem enough to pay.
   - A lifetime or retention figure is evidence only if the data covers that long and every
     customer. A six-month average from a three-month pilot, or from "the ones who stuck
     with it", is an assumption; the real lifetime is unknown and probably shorter.

3. **Test the claimed unfair advantage.** An unfair advantage can't be copied or bought by a
   funded competitor within a year: insider information, an existing audience or customer
   base, a network effect, a community, exclusive access or contract, a team member's
   authority. A feature, an algorithm, "AI", "first mover", "better UX" or "passion" is not
   one; it moves to Solution or UVP. Write ✅ *"Unfair advantage: none yet. The folding
   repair stand is a feature — any mechanic can buy or copy one. A candidate: exclusive
   access to office car parks, if landlords grant it."* ❌ *"Unfair advantage: our
   proprietary stand design."*

4. **Check every channel against the early adopter.** For each stated channel, ask: do these
   people go there? A channel aimed at a different buyer (a procurement conference for ward
   nurses who buy nothing themselves, Instagram ads for commuters the input says are offline
   all day) is a mismatch. Name it, and say who the channel does reach. If **no** stated channel reaches the early adopter, that is a change-before-building
   finding (step 7).

5. **Compute the unit economics when price and costs are given.** Never estimate. Run:

   ```bash
   # Claude Code
   python3 "${CLAUDE_SKILL_DIR}/scripts/unit_economics.py" --price 12 --variable-cost 7 --cac 90 --lifetime 6 --fixed 6000
   # Other IDEs (from the skill folder)
   python3 scripts/unit_economics.py --price 12 --variable-cost 7 --cac 90 --lifetime 6 --fixed 6000
   ```

   Derive inputs from what the user gave and show the derivation (✅ *"CAC $90 = $900 ad
   spend ÷ 10 sign-ups"*). Use one currency and one period throughout. Add `--churn` instead of `--lifetime` when churn is given,
   `--market-customers` when the user sizes the market. The script returns gross margin,
   LTV, CAC payback, LTV:CAC, the most a customer can cost to acquire, break-even customers
   and where the numbers don't close. If no script can run, do the same arithmetic by hand
   and show every line. Price or cost missing → skip this step, list what's missing under
   "To confirm", and write no number the user didn't give.

6. **Rank the assumptions by risk = likelihood wrong × impact if wrong.** Likelihood: high
   (no evidence, wrong-segment evidence, or opinion only), medium (right segment but few
   people or indirect), low (observed behaviour from the right segment). Impact: fatal (the
   idea fails), pivot (a box has to change), tune (a number moves). Score 3/2/1 each and sort.
   The riskiest assumption sits in problem, customer or channel far more often than in
   solution, because a solution can be rebuilt in a sprint while a problem nobody has can't
   be fixed by building. Say in one sentence why the top one beats the others **for this
   idea**. A solution assumption ("can the matching algorithm be accurate?") ranks first only
   when the problem and customer are already backed by behaviour. Ties: the assumption the
   others depend on goes first (a channel test means nothing until the problem holds).

7. **Say plainly when the idea should change before anything is built.** Triggers: no stated
   channel reaches the early adopter; CAC payback is longer than the customer lifetime;
   break-even needs more customers than the stated market holds; the only problem evidence is
   from a different segment. Write one sentence per trigger with what has to change.
   ✅ *"Change before building: each member costs $90 to acquire and returns $30 over six
   months, so every sign-up adds a $60 loss."* Silence on a finding the numbers show is a
   failure. An assumption the user's own numbers already disprove is a finding here, not a
   test to run: a $90 CAC against a $10 ceiling needs a new channel, not more of the old one.

8. **Design the cheapest test that could prove each of the top 1–3 assumptions wrong.**
   Each test names: what to do, the sample, the pass/fail line **set before running**, the
   cost, the time, and what changes if it fails. Use counts, not percentages, for small
   samples. Take thresholds from step 5 where possible (the most a customer can cost to
   acquire is the channel test's fail line). Test menu and interview rules in
   [`reference.md`](reference.md).
   - ✅ *"Stand at two office bike racks for a morning and ask 20 cyclists about the last
     time their bike needed fixing; never pitch. If fewer than 6 paid for a repair in the
     past three months, the problem is wrong. Cost: $0. Time: two mornings."*
   - ✅ *"Put a sign-up sheet with the $12 price and a card form at one rack for a week. Fail
     if fewer than 5 of the cyclists who stop pay the first month."*
   - ❌ *"Validate the market."* ❌ *"Run a survey to gauge interest."* ❌ *"Build an MVP and see."*

9. **Write the reply in this order.** Keep it lean: under about 500 words unless a document
   was asked for, and shorter when the user says "quick" or "short".
   1. **Riskiest assumption and its test**: two to four lines, first in the reply.
   2. **Change before building**: one line per trigger from step 7, or omitted when none fired.
   3. **Canvas**: nine rows, one line each, every entry tagged.
   4. **Next assumptions and tests**: numbers 2–3, same shape as the first, with the risk score.
   5. **Unit economics**: the computed lines and the flags, only when step 5 ran.
   6. **To confirm**: what was missing, once.

**Non-interactive runs** (subagent, CI, headless): a missing early adopter, channel or price
is not asked about; the most defensible reading of the input is used, tagged `[assumption]`,
and ranked as an assumption to test. No idea at all — no problem and no customer — emits
`BLOCKED: need the idea: who has the problem and what the problem is`, because a canvas of
invented boxes tests nothing.

## Useful references in this skill

- [`reference.md`](reference.md) — the test menu, how to set a pass/fail line, interview rules, what counts as an unfair advantage, internal-product reading of the boxes
- [`scripts/unit_economics.py`](scripts/unit_economics.py) — gross margin, LTV, CAC payback, break-even customers and the flags (stdlib only)
- [`examples/bike-repair.md`](examples/bike-repair.md) — worked example: an on-site bike repair subscription where the payback outruns the lifetime

## Quality bar

- **The first lines are the riskiest assumption and its test**, not the canvas.
- **Every canvas entry carries a tag**, and every `[evidence]` names the source the user gave.
- **Wrong-segment and opinion-only evidence is downgraded** and said to be.
- **A feature claimed as an unfair advantage is moved out**, and the box reads "none yet" if nothing else qualifies.
- **Each channel is checked against the early adopter**, mismatches named.
- **Unit economics are computed with the derivation shown**, and payback longer than lifetime is flagged.
- **Each top test has a sample, a pre-set pass/fail line, a cost and a time.**
- **Nothing is invented**: no market sizes, competitors, prices, churn or channels the user didn't give.

## When to use this skill

- ✅ A founder's or intrapreneur's idea in their own words: "is this worth building?"
- ✅ "Fill in a lean canvas for…" or "what are my riskiest assumptions?"
- ✅ Planning what to test before writing code or asking for budget
- ✅ An internal tool pitch where adoption by another team is the real bet

## When NOT to use this skill

- ❌ An investment case with options, NPV, payback ranges and a sponsor — `business-case`
- ❌ The press release and FAQ for an idea that is already approved — `prfaq`
- ❌ Market attractiveness, competitors, SWOT or Five Forces — `strategy-analysis`
- ❌ How to measure a feature that has shipped or is about to — `success-metrics`
- ❌ Turning interview notes or tickets already collected into themes — `feedback-synthesis`

## Anti-patterns to avoid

- ❌ **The tidy grid.** Nine confident boxes and no ranking: the founder learns nothing they didn't write.
- ❌ **Accepting the moat.** "Our AI" as unfair advantage. Funded competitors copy features.
- ❌ **Counting "they'd use it" as evidence.** Opinion about the future is the weakest signal there is.
- ❌ **Estimating the economics.** "Margins look healthy" when a $90 CAC against $30 of lifetime margin loses money on every customer.
- ❌ **Riskiest assumption = will the tech work.** The usual killer is that the people can't be reached or don't care enough to pay.
- ❌ **Tests with no fail line.** "Talk to some customers" can't fail, so it can't teach.
- ❌ **Inventing a channel or a market size** to make a box look complete.
- ❌ **Burying "change this first"** under the canvas, or leaving it out to be encouraging.
