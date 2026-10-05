---
name: cloud-cost-review
description: Review actual cloud spend from a cost export (AWS CUR or Data Exports, GCP billing export, Azure cost details) and produce a ranked savings report — idle and unattached resources, oversized instances backed by utilisation evidence, storage tiering, data transfer hot spots, commitment coverage and untagged spend — each finding with a monthly saving computed from the bill, a confidence level and an ease rating. Use when the user shares a cost CSV and says "where are we wasting money", "review our AWS bill", "why did the cloud bill jump this month", "find savings in our GCP/Azure spend", or "should we buy savings plans".
---

# cloud-cost-review

Reads what the organisation actually spent, from a billing export, and produces a short list of savings ranked by size and effort. A script aggregates the export: totals by service, account and tag, month-over-month change, top movers, hot spots, untagged share and commitment coverage. The skill turns that into findings. Each finding has a saving worked out from the bill, a confidence level, and the evidence still needed before anyone acts.

This looks backward at a real bill. `capacity-cost-model` looks forward: it sizes a service from a demand driver before launch and projects cost at 1×, 3× and 10×. If the user has no bill yet, or asks "what will this cost", that is `capacity-cost-model`.

## How to respond

1. **Ask once for what is missing, then proceed.** Ask at most 2 questions:
   - **The export and its source** (AWS CUR or CUR 2.0, GCP billing export, Azure cost details, or something else). The script detects the format from the header. Cost Explorer's "Download CSV" is a summary, not line items. Ask for CUR or Data Exports, or reshape it to the generic layout in [`reference.md`](reference.md).
   - **The tag keys that carry ownership** (for example `team`, `env`, `cost-center`). Without one, untagged share can't be measured.
   Default to the latest month in the file compared with the month before it. Two months of daily data is the minimum for a useful review. Say so if the file has less.

2. **Run the script and read its output before writing findings.**

   ```bash
   # Claude Code
   python3 "${CLAUDE_SKILL_DIR}/scripts/cost_summary.py" cost.csv \
     --tag team --tag env --top 10 --out out/cost-summary.md --json out/cost-summary.json

   # Other IDEs (from the skill folder)
   python3 scripts/cost_summary.py cost.csv \
     --tag team --tag env --top 10 --out out/cost-summary.md --json out/cost-summary.json
   ```

   - Check the "Column mapping used" section. If a field mapped to the wrong column, or didn't map, rerun with `--format` or rename the column. Don't reason from a mis-mapped total.
   - Read the notes:
     - A partial month means change columns are per day.
     - A monthly-grain export can't show a steady on-demand floor.
     - Missing tag keys mean the tag name is wrong.
   - Exit 2 means bad input: the file, line and problem are in the message. Fix the input and rerun.

3. **Check each category in [`reference.md`](reference.md) against the output.** For each one, read the evidence the bill gives and name the evidence it doesn't:

   | Category | What the bill shows | What it can't show, and where to get it |
   |---|---|---|
   | Idle and unattached | Idle address lines, volumes and snapshots with steady cost | Whether a volume is attached or an IP is in use: the provider CLI (commands in the reference) |
   | Oversized instances | Instance type, hours, cost | CPU and memory use. Get two or more weeks of CPU and memory metrics, or a rightsizing tool's report. **No evidence, no saving figure.** |
   | Storage tiering | Storage class line items and their growth | Access pattern: storage analytics or access logs |
   | Data transfer hot spots | NAT, inter-zone, inter-region and egress lines and their movement | Source and destination: flow logs |
   | Commitment coverage | On-demand vs covered compute, utilisation, daily on-demand floor | Future plans for the workload: ask the owner |
   | Untagged spend | Untagged share, of all spend and of spend with a resource id | Who owns it: the account or project owner |

4. **Estimate each saving from the bill, and show the arithmetic.**
   - ✅ *"Two always-on m6i.2xlarge web instances cost $552.96/month on demand. This bill shows the existing savings plan covering the same type at 31.0% below on-demand ($190.80 effective vs $276.48 on-demand equivalent). Covering both saves about $171/month."*
   - ❌ *"Buying savings plans could save 30–70%."* That is a brochure range, not this bill.
   - Take discount rates from the user's own bill, the provider's recommendation report, or a price the user supplies. If none of those exist, give the formula and leave the rate as an input. Never type a list price from memory.
   - A finding whose saving can't be computed from the evidence at hand goes in **Evidence needed**, with what to collect. It doesn't get an invented number.

5. **Rate confidence and ease, then rank.**
   - **Confidence:**
     - **High:** the bill alone proves it (an idle-address line, a measured coverage gap).
     - **Medium:** one fact still needs checking (is the volume attached?).
     - **Low:** depends on evidence not yet collected.
   - **Ease:**
     - **3:** a config change or deletion, no service impact.
     - **2:** a change that needs a test or a maintenance window.
     - **1:** a re-architecture, or a purchase that needs approval.
   - Rank by monthly saving × ease, and show confidence next to each finding.
   - Then set the order of work: waste removal comes before any commitment purchase, whatever their ranks. Size a commitment on the on-demand floor that is left after cleanup. Committing to spend you are about to delete locks in the waste.

6. **Explain the month-over-month change in one paragraph.** Start from the top movers. ✅ *"Usage rose $1,481 (+24.4%). $1,099 of that is NAT gateway data processing in account 111111111111."*

7. **Emit the report** with [`templates/cost-review.md`](templates/cost-review.md):
   - the scope line (export, months, cost basis)
   - the month-over-month paragraph
   - the ranked findings table
   - each finding with evidence, arithmetic, confidence, ease and the action
   - evidence needed
   - untagged spend and ownership
   - what was excluded (tax, credits, commitment fees)
   Hand a logging or metrics cost hot spot to `observability-plan` for a telemetry budget. Hand a forward projection to `capacity-cost-model`.

**Non-interactive runs** (subagent, CI, headless): the month defaults to the latest in the file, and a missing tag key means untagged share is reported as "not measured". Both are tagged `[assumption]` at the top. With no export, emit `BLOCKED: need a cost export CSV (AWS CUR/Data Exports, GCP billing export, Azure cost details, or the generic layout)`. Never produce a saving figure that the script output and the stated evidence don't support.

## Useful references in this skill

- [`reference.md`](reference.md): field mapping for each provider's export, how line-item types are treated, the evidence each category needs and how to get it, saving formulas, and the confidence and ease scales
- [`templates/cost-review.md`](templates/cost-review.md): the report skeleton
- [`examples/acme-aws-september.md`](examples/acme-aws-september.md): the sample CUR export in this folder, the script's real output, and the review written from it
- [`scripts/cost_summary.py`](scripts/cost_summary.py): the aggregator (stdlib, Python 3.9+)

## Quality bar

- **Every amount traces to the script output or to arithmetic shown in the finding.** No list prices from memory, and no "industry average" savings percentages.
- **Rightsizing needs utilisation evidence.** An instance finding without CPU and memory data goes under Evidence needed, not in the ranked table.
- **Each finding has a monthly saving, a confidence level and an ease rating**, or sits in Evidence needed with what to collect.
- **Ranked by saving × ease, and sequenced so waste removal happens before any commitment purchase.**
- **The month-over-month change is explained by named movers**, not described as "costs went up".
- **Untagged share is reported** both against all spend and against spend that has a resource id, because data transfer and support lines often can't be tagged.
- **Excluded lines are stated.** Tax, credits, refunds and commitment fees are listed separately so the review doesn't hide credits that mask waste.

## When to use this skill

- ✅ "Here's our CUR for August and September. Where's the waste?"
- ✅ "Why did the bill jump this month?"
- ✅ Deciding whether to buy more savings plans, reserved instances or committed use discounts.
- ✅ Measuring untagged spend before a chargeback or showback rollout.

## When NOT to use this skill

- ❌ Estimating cost before launch, or projecting at 3× or 10× growth. Use `capacity-cost-model`.
- ❌ Designing telemetry or a logging budget from scratch. Use `observability-plan`, though this skill flags logging cost as a hot spot.
- ❌ Writing up an incident, including a cost spike from a runaway job. Use `postmortem-generator`.
- ❌ Reporting AI tool usage or spend by user. Use `ai-usage-report`.
- ❌ Defining business KPIs for a feature or product. Use `success-metrics`.

## Anti-patterns to avoid

- ❌ **Rightsizing from the bill alone.** An r6i.4xlarge costing $726/month says nothing about whether it is busy. Get the utilisation data.
- ❌ **Committing before cleaning up.** Sizing a savings plan on an on-demand floor that includes a staging box you are about to stop locks in waste for a year or more.
- ❌ **Brochure percentages.** "Spot saves up to 90%" is not a finding about this bill.
- ❌ **Netting credits into usage.** A $250 credit makes a wasteful month look flat. Keep credits on their own line.
- ❌ **Comparing a partial month with a full one.** Ten days of October against all of September always looks like a saving.
- ❌ **Treating all untagged spend as a tagging failure.** Data transfer without a resource id can't carry a tag. Report it separately.
- ❌ **A 40-item list.** Five findings with real numbers get acted on. Forty with guesses don't.
