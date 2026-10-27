# lean-canvas reference

Long-form material for the steps in `SKILL.md`. The canvas is Ash Maurya's adaptation of the
Business Model Canvas (*Running Lean*); the interview rules follow Rob Fitzpatrick's *The Mom
Test*.

## The nine boxes, in the order to fill them

| Box | What goes in | Common wrong entry |
|---|---|---|
| Problem | The top 1–3 problems, and how the early adopter copes today (existing alternatives) | A solution phrased as a problem: "no app for X" |
| Customer segments | Who has the problem; the **early adopter** named separately, narrow enough to find by name | "Small businesses", "everyone who…" |
| Unique value proposition | One sentence: why this, for the early adopter, instead of what they do today | A feature list |
| Solution | The smallest thing that addresses each problem | A roadmap |
| Channels | The paths to the early adopter, free and paid | Channels that reach the later segment |
| Revenue streams | Price, who pays, how often | "Freemium" with no paid tier defined |
| Cost structure | Cost to serve one customer, fixed costs, acquisition cost | Fixed costs only |
| Key metrics | The 1–3 numbers that show the model works (activation, retention, paid conversion) | Downloads, page views |
| Unfair advantage | What a funded competitor can't copy or buy within a year | A feature, "AI", "first mover", "passion" |

**Internal products.** Revenue streams = the budget line or measured saving that keeps it
funded. Customer = the team that has to change how it works; early adopter = the one team
with the worst version of the problem and a lead who asked for help. Channel = how that team
hears about and gets onto the tool (a mandate, a team lead, an existing workflow it plugs
into). Unfair advantage can be real here: access to internal data or a mandate no vendor
has. Still test whether the team will change its habits.

## Grading evidence

| Signal | Grade |
|---|---|
| Paid, pre-ordered, signed a letter of intent, or switched from a current tool | Behaviour — strongest |
| Describes a recent, specific instance of the problem unprompted, and what it cost | Behaviour about the past — strong |
| Built a workaround (spreadsheet, hired someone) | Behaviour — strong |
| "I'd definitely use it", "great idea", survey interest | Opinion — weak, counts as assumption |
| Industry statistic or report | Sizes the market; says nothing about this segment's willingness to pay |
| Any of the above from a segment other than the early adopter | Counts as assumption for the early adopter |

## Scoring risk

| | Fatal (3) | Pivot (2) | Tune (1) |
|---|---|---|---|
| **High (3)** — no evidence, wrong segment, opinion only | 9 | 6 | 3 |
| **Medium (2)** — right segment, few people or indirect | 6 | 4 | 2 |
| **Low (1)** — observed behaviour, right segment | 3 | 2 | 1 |

Ties: rank the assumption whose test is cheaper first; it clears the way for the rest.

Why problem, customer and channel usually top the list: a wrong solution is fixed by
rebuilding it, which a team can do in weeks. A wrong problem or an unreachable customer means
the next build lands on nobody, and no amount of engineering moves it.

## Test menu, cheapest first

| Test | Proves wrong | Typical sample | Typical cost and time |
|---|---|---|---|
| Problem interview | The problem, the segment | 10–20 early adopters | $0–$200, 1–2 weeks |
| Channel smoke test | The channel and its cost | $100–$500 of spend or one week of outreach on one channel | the spend, 1 week |
| Landing page with a price | The UVP and the price | 100+ visitors from the stated channel | $100–$500, 1–2 weeks |
| Concierge run (deliver it by hand) | The solution and retention | 3–10 customers | founder time, 2–4 weeks |
| Pre-sale or letter of intent | Willingness to pay | 5–20 asks | $0, 2–4 weeks |
| Wizard of Oz (looks automated, done by hand) | The solution at small volume | 10–30 uses | founder time, 2–4 weeks |

A survey and "build an MVP and see" are not on the menu: the first measures opinion, the
second costs months to learn what an interview learns in a week.

## Setting the pass/fail line

- **Write it before the test runs**, as a count: "fewer than 4 of 10". A line set after the
  results arrive moves to fit them.
- **Take it from the numbers when they exist.** Channel test fail line = the most a customer
  can cost to acquire (lifetime margin ÷ 3 for a business that has to cover fixed costs;
  lifetime margin at break-even). Landing-page fail line = the conversion that would
  produce that cost per customer at the channel's cost per visitor.
- **No numbers yet:** a problem interview passes when at least 4 in 10 describe a recent
  instance unprompted; a pre-sale passes when at least 1 in 5 pays or signs.
- **Say what failure changes:** which box is rewritten, and what the next test is.

## Problem-interview rules

1. Ask about the past, never the future. ✅ "When did that last happen? What did you do?"
   ❌ "Would you use an app that…?"
2. Don't pitch until the end, if at all. The moment the idea is described, people are polite.
3. Ask what it cost them: time, money, a lost customer.
4. Ask what they do about it today and what that costs. No workaround is a warning sign.
5. Count who raised the problem **before** it was named, separately from who agreed once asked.

Five-question script: "Walk me through your last [day/week/job]." / "What was the hardest
part?" / "When did [problem area] last go wrong? What happened?" / "What did you do about
it, and what did that cost?" / "What have you tried to fix it?"

## What counts as an unfair advantage

Counts: insider information, an existing audience or customer base, a network effect,
a community, exclusive contracts or access, regulatory permission others lack, a team
member whose name opens doors in this market, internal data or a mandate (internal products).

Doesn't count: a feature, an algorithm, "AI", a patent pending on a feature, first-mover,
better UX, lower price, hard work, passion. These go in Solution or UVP.

"None yet" is the most common correct answer at this stage. Name a candidate the idea
could grow into, if the input supports one.
