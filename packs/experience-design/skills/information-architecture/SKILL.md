---
name: information-architecture
description: Design the information architecture for a product or site — a content inventory grouped by how users think, labels in their words, a navigation model split into global, local and utility nav, an indented sitemap plus a Mermaid diagram, a label rationale table, the findability risks, and the card-sort or tree-test plan that would validate it. Use when the user wants a sitemap, IA, navigation structure, menu design, "reorganise our help centre", "where should this page live", or says users "can't find anything".
---

# information-architecture

Produces the structure underneath the screens: what content exists, how it groups, what each group is called, and how people move between groups. The output is a sitemap someone can build navigation from, plus the test that would prove users can find things in it. Sits below `user-journey-map` (which says what people are trying to do) and above `content-design` (what one page says) and `ux-writing` (the exact strings). A structure nobody has tested is a hypothesis; this skill says so and ships the test.

## How to respond

1. **Get the inputs in one message.** Ask at most 2 questions, spent on the weakest of: *who the main audiences are and their top tasks*, and *what content exists today* (a page list, current menu, URL export, or feature list). Default everything else: web, desktop and mobile, existing content kept unless obviously dead. With no content list, build the inventory from what the user described and mark it `[inferred]`.

2. **Inventory before structure.** List every content item or feature as a flat table: item, type (task, reference, marketing, account, legal), audience, and a status (`keep` / `merge` / `cut` / `[inferred]`). Grouping comes after the list, never before it. Why: starting from the old menu copies its mistakes into the new one.

3. **Group by user task and mental model, not by org chart.** ✅ *"Get paid", "Manage your team", "Taxes"* — ❌ *"Finance Ops", "People Platform", "Compliance Team"*. Pick one organising scheme per level and say which: task, audience, topic, or object. Mixing schemes at one level ("Products", "For developers", "Pricing", "Help") is the most common IA defect; when audience-based top-level nav is unavoidable, say why and flag the overlap risk.

4. **Label in the user's words.** Each group label is the term users would type into search or say aloud. Prefer short, concrete nouns or verb phrases; no internal product names unless users already know them; no "Solutions", "Resources" or "More" as a bucket. Record every label decision in the rationale table: label, what it holds, why this word, rejected alternatives, and the evidence (`[search logs]`, `[support tickets]`, `[interview]`, `[assumption]`).

5. **Split the navigation model into three systems:**
   - **Global nav** — 5–7 top-level items, present on every page. More than 7 means the grouping is not done.
   - **Local nav** — the sections within one global area (sidebar, tabs, sub-menu).
   - **Utility nav** — account, settings, help, search, language, sign out. Kept out of global nav.
   Also name cross-links (related content that lives elsewhere) and the search role: search backs up navigation, it does not replace it.

6. **Keep depth and breadth honest.** Default to 3 levels or fewer for anything users reach weekly. Put the top 3 tasks one click from the home or landing page. Flag every item that sits in two places (allowed for cross-links, not as two homes) and every group with one child (merge it up) or more than ~10 (split it).

7. **Name the findability risks.** For each risk: the item, why users will look in the wrong place, the severity (🟥 top task affected / 🟧 frequent task / 🟨 rare task), and the mitigation (cross-link, rename, move, search synonym). Ambiguous labels, overlapping groups and items that fit two parents are the usual sources.

8. **Write the validation plan** from [`reference.md`](reference.md): an **open or hybrid card sort** when the grouping or labels are unproven, a **tree test** when the structure exists and needs proving. The tree test gets 6–10 tasks written as user goals without the label words in them (✅ *"You were charged twice this month. Where would you go?"* — ❌ *"Find Billing"*), each with the correct destination and a pass threshold. State participants and what result would change the structure.

9. **Emit with [`templates/ia-spec.md`](templates/ia-spec.md)** in one message: audiences and top tasks, inventory, organising scheme per level, the indented sitemap tree, the Mermaid diagram, the nav model, the label rationale table, findability risks, and the validation plan. Hand-offs: page-level content for a key page → `content-design`; menu and button strings → `ux-writing`; requirements for a new section → `prd-draft`. See [`examples/payroll-app-nav.md`](examples/payroll-app-nav.md).

**Non-interactive runs** (subagent, CI, headless): a missing content list becomes an `[inferred]` inventory and missing audiences become `[assumption]` lines at the top. If neither the product nor its content can be identified from the input, emit `BLOCKED: need the product and its content or features` and build nothing.

## Useful references in this skill

- [`reference.md`](reference.md) — organising schemes, card sort and tree test methods, participant counts, metrics and pass thresholds, label tests
- [`templates/ia-spec.md`](templates/ia-spec.md) — the IA spec skeleton: inventory, tree, Mermaid, nav model, rationale and risk tables, validation plan
- [`examples/payroll-app-nav.md`](examples/payroll-app-nav.md) — worked example: a cluttered payroll app menu restructured around tasks

## Quality bar

- **The inventory exists and comes first.** Every item in the sitemap traces to an inventory row; every `cut` is listed, not silently dropped.
- **One organising scheme per level**, named. Mixed schemes are flagged with the reason.
- **Labels are user words with a recorded reason.** Every global and local label appears in the rationale table with its evidence tag.
- **Global nav has 5–7 items; utility items are not in it.**
- **Top tasks are one click from the landing page** and depth is 3 levels or fewer for weekly tasks, or the exception is stated.
- **The tree and the Mermaid diagram match** node for node, and the Mermaid renders.
- **Findability risks are named with severity and a mitigation.**
- **The validation plan has tasks written without label words**, correct destinations, a threshold, and what result would change the design.
- **Nothing is invented.** Content items, audiences and evidence not in the input are tagged `[inferred]` or `[assumption]`.

## When to use this skill

- ✅ A new product, site, app or help centre needs a sitemap and navigation
- ✅ "Users can't find anything" — restructuring an existing menu or content set
- ✅ Merging two products or sites into one navigation
- ✅ Deciding where a new feature or section should live

## When NOT to use this skill

- ❌ The steps and emotions of one persona reaching an outcome — that's `user-journey-map`
- ❌ What one page should say and in what order — that's `content-design`
- ❌ The exact wording of menu items, buttons and errors across a flow — that's `ux-writing`
- ❌ The requirements and scope of a new feature — that's `prd-draft`

## Anti-patterns to avoid

- ❌ **The org chart as navigation.** Groups named after the teams that own them. Users don't know your teams.
- ❌ **"Resources", "Solutions", "More".** A bucket label means the grouping stopped before it finished.
- ❌ **Redrawing the old menu.** Skipping the inventory and rearranging the existing items keeps every old overlap.
- ❌ **Two homes for one item.** An item that lives in both "Settings" and "Team" will be maintained in one and stale in the other. One home, cross-links elsewhere.
- ❌ **Search as the fix.** "They can search for it" hides a structure problem; search logs full of nav-label queries are the symptom.
- ❌ **Tree-test tasks that give away the answer.** "Find the Invoices page" tests reading, not findability.
- ❌ **Presenting an untested structure as final.** Tag it a hypothesis and ship the test with it.
