# information-architecture — reference

## Organising schemes

Pick one per level. Name it in the spec.

| Scheme | Groups by | Works when | Breaks when |
|---|---|---|---|
| Task | What the user is trying to do ("Get paid", "Hire") | Products people use to get jobs done | Tasks overlap heavily, or the content is mostly reference |
| Topic / subject | What the content is about ("Taxes", "Benefits") | Help centres, knowledge bases, content sites | Topics are org terms users don't share |
| Audience | Who it's for ("For employers", "For employees") | Audiences need almost entirely different content | Most content serves several audiences; users can't tell which bucket they're in |
| Object | The thing being managed ("Invoices", "People", "Projects") | Tools where users manage records | Users think in tasks that span objects |
| Exact (alphabetical, chronological, geographic) | A known ordering | Users already know the item name, date or place | Users are browsing, not looking up |

Mixed schemes at one level ("Products / Developers / Pricing / Help") make users guess which axis to try first. If you must mix, put the odd one in utility nav or a footer.

## Card sorting — when the grouping or labels are unproven

- **Open sort:** participants group cards and name the groups. Use it to learn users' categories and words. Output: common groupings, the labels participants wrote, cards with no agreed home.
- **Closed sort:** participants place cards into groups you name. Use it to check whether proposed groups are understood.
- **Hybrid:** proposed groups, but participants may add their own. A sensible default for a redesign.
- **Cards:** 30–60 items from the inventory, written in plain words, not the current labels.
- **Participants:** a common rule of thumb is around 15 per distinct audience for an open sort; more for closed sorts if you want to compare percentages.
- **Read the results:** look at agreement on which cards go together, and at the cards that split across groups. Split cards are the findability risks.

## Tree testing — when the structure exists and needs proving

A tree test shows participants the text-only hierarchy (no visual design) and asks them where they would go to complete a task.

- **Tasks:** 6–10, written as goals in the user's situation. Never use the label words. Cover the top tasks and the riskiest items from the findability table.
- **Each task records:** the correct destination(s), and which risk it tests.
- **Metrics:**
  - *Success rate* — reached a correct destination.
  - *Directness* — got there without backtracking.
  - *First click* — the first top-level choice. A wrong first click predicts failure.
  - *Time* — secondary; use it to compare versions.
- **Thresholds (set before running):** a common starting point is 70%+ success for top tasks and 80%+ correct first click; set your own and write it down before seeing results.
- **Participants:** tree tests are usually run unmoderated with a larger sample than card sorts (often 50 or more) so per-task percentages are stable.
- **Decision rule:** name what changes if a task fails — rename the label, move the item, add a cross-link — before you run it.

## Label tests

A label passes when:
- a user would say or type it (check search logs and support tickets if available);
- it is distinct from its siblings (no two labels a user could confuse);
- it predicts what's inside (no surprise on click);
- it is short enough for the nav slot (aim for 1–3 words in global nav);
- it is consistent with the terminology list, if `ux-writing` has produced one.

## Depth and breadth

- Broad and shallow beats narrow and deep for things people use often; each extra level is another chance to choose wrong.
- Fewer than 3 or more than ~10 children in a group is a signal to merge or split.
- The global nav limit of 5–7 is a working default for scannability, not a law; exceed it only with a stated reason.
