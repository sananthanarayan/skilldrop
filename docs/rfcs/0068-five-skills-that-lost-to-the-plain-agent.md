---
rfc: 0068
title: Keep, rebuild or retire the five skills that lost to the plain agent in both trials
status: implemented
date: 2026-10-27
author: sanjay-ananth
---

# RFC-0068: Keep, rebuild or retire the five skills that lost to the plain agent in both trials

## Problem / use case

The scripts-only benchmark ([RFC-0067](0067-scripts-without-instructions.md)) ran two trials of
every scripted skill's held-out evals on `claude-sonnet-5-5`, with two blind judges. Five skills
lost to the plain agent in each trial, with both judges: `deck-builder`, `file-to-markdown`,
`marketing-flyer`, `md-to-html` and `mermaid-render`. That is the roadmap's bar for asking the
RFC-0046 question of each: **what rule does this skill add that the plain agent breaks?**

## Evidence

One analyst per skill read:
- the skill's folder;
- every output of the three arms (skill, scripts only and plain agent), including the files
  each left behind;
- every assertion result, and every judge's reason.

The list of five was fixed before any reason was read.

| Skill | Pairs won against the plain agent (judge 1, judge 2, of 4) | What the files showed | Rule it adds that the plain agent broke | Verdict |
|---|---|---|---|---|
| `md-to-html` | 0, 0 | The plain agent's page was better in 4 of 4 runs. The skill's script showed a raw iframe and script as text, its security policy blocked an embed, and it rejected a brand file that gave fonts as plain names | None. The agent removed scripts, embedded images and named what was missing in 4 of 4 | **Retire** |
| `mermaid-render` | 0, 0 | All three arms fixed the same diagrams. The plain agent called the Mermaid CLI itself and said plainly what it hadn't rendered. The scripts-only arm shipped a CDN-loading HTML page twice | None, 0 of 4. The skill added a lint and a report the judges called unsupported or unasked | **Retire** |
| `marketing-flyer` | 0, 0 | In one eval the skill built nothing: its non-interactive rule stopped it for one missing image. In the other it filled a generic template. The plain agent built the whole flyer with visible placeholders | None. The agent invented nothing in 4 of 4. The skill's one effective rule was the one that lost | **Retire** |
| `file-to-markdown` | 0, 0 | The script wrote an unaccepted tracked insertion as settled text and dropped an embedded image. The plain agent converted the .docx by hand from its XML, correctly. In a "just the table" request the skill kept a total it had flagged as wrong | None, 0 of 4. Both losses come from the script's defaults | **Rebuild**, then re-measure |
| `deck-builder` | 0, 0 | Not a fair test. The script needs `python-pptx`, which the sandboxed run couldn't install, so the skill and scripts-only arms delivered a plan and no file in 8 of 8 runs. The plain agent wrote a valid .pptx with the standard library every time. Slide content was equally good | At most 1 of 4 runs | **Rebuild**, then re-measure |

## Proposal

**Retire `md-to-html`, `mermaid-render` and `marketing-flyer`, as RFC-0046 retires a skill.**
- **The record:** each folder is deleted, and `catalogue.json` records the retirement with its
  reason. `outdated`, `update` and `doctor` name an installed copy with the reason and the
  uninstall command, and remove nothing.
- **Other skills stop pointing at them:**
  - `brand-kit`, `interactive-diagram`, `file-to-markdown`, `md-to-docx`, `md-to-pptx` and
    `md-to-confluence` drop their `related` and `handoff` entries.
  - The converters' "render it to PNG" step now names the Mermaid CLI directly.
- **The packs:**
  - The design pack is now about decks: its first task builds one, where it used to make a
    flyer.
  - The converters pack's journey drops its HTML and Mermaid steps, and the tutorial's HTML
    section becomes a slide-deck section, with real output from `md-to-pptx`.
- **The record count:** the share card's "4 retired" becomes 7.

**Rebuild `file-to-markdown` and `deck-builder` rule-first, then measure each on fresh blind
evals.** Each keeps its scripts. The rules below are general, not fitted to the evals above:
- **`file-to-markdown`:**
  - Extract an embedded image beside the Markdown and link it, instead of dropping it.
  - Write a tracked change as pending (insertion and deletion both shown and marked), never as
    settled text.
  - Keep a figure the source contradicts out of a table meant to be pasted, and say why.
- **`deck-builder`:**
  - Deliver the file the request names. When a dependency can't be installed, build the deck
    another way and say what was lost; never end with only a plan or a spec.
  - Put a flagged figure on the slide with its caveat, not only in chat.
  - Cut the audience table, the setup block and the "To confirm" list.
  - **The benchmark half:** it installs a skill's declared pip requirements before a run,
    which is what a user does.

Each rebuild faces the same bar as an admission. If it still loses to the plain agent, it is
retired.

## Alternatives considered

- **Fix the scripts of the three being retired.** `md-to-html`'s defaults could be repaired,
  but the plain agent wrote a better page by hand in every run and broke no rule the skill
  teaches. A repaired script would still add nothing the model lacks.
- **Retire `file-to-markdown` too.** Its script is also the benchmark's Office-file viewer and
  a fuzz target, and both losses came from defaults that can be fixed. Its evals covered only
  .docx and .csv, not the formats where a parser matters most (.msg, scanned PDF, large
  .xlsx).
- **Retire `deck-builder` because `md-to-pptx` exists.** They do different jobs: `md-to-pptx`
  converts a document, while `deck-builder` designs a deck with native charts and a corporate
  template. Neither was tested here. It deserves a run in which its script can work.

## What the rebuilds measured

Each rebuild was measured on two new held-out evals, written blind from its description after
the rebuild. Two trials, two judges, model `claude-sonnet-5-5`, $3.52 for both. The benchmark
now installs a skill's pip requirements into an environment on every arm's PATH, which is what a
user does, so `deck-builder`'s script could run this time.

| Rebuild | Evals | Judge 1 | Judge 2 | Checks met | Plain agent | Result |
|---|---|---|---|---|---|---|
| `file-to-markdown` 0.4.0 | 5–6 | 2 of 4 | 3 of 4 | 72% | 62% | **Kept** |
| `deck-builder` 0.4.0 | 6–7 | 2 of 4 | 1 of 4 | 69% | 81% | **Retired** |

- **`file-to-markdown` passes.** On the workbook-and-deck eval both judges preferred it in both
  trials: it converted both files faithfully and caught a stated total that didn't match its
  parts. On the tracked-changes eval the plain agent was preferred three times out of four. Both kept
  the changes pending. The judges' reasons were that the plain agent also kept the reviewer's
  comment and who made each change, which the script still reports as dropped.
- **`deck-builder` still loses with its script working.** It built on the template and put the
  caveats on the slides. The judges still preferred the plain agent's decks in most pairs, and
  the plain agent met more of the checks. So it is retired, as the bar says.
- **One rebuild draft was caught leaking.** Three lines first written into `deck-builder`'s
  instructions echoed the new evals' summary, which had been read minutes earlier. They were
  removed before the run, and a scan of both diffs against the new evals found no overlap beyond
  everyday words.

**What retiring `deck-builder` leaves.** The design pack keeps `brand-kit` and `slide-outliner`.
It now ends with a reviewed outline, which `md-to-pptx` turns into a `.pptx` with the same
`brand.json`. `brand-kit`'s output is read by the Word and PowerPoint converters. Native
PowerPoint charts and building on a corporate `.potx` template go with it. The roadmap can
revisit them as a new skill measured from the start.

**`figma-diagrams` also has a pip requirement,** so its scripts-only reading on 27 October was
taken without its package installed. It should be re-run with the new environment before
anything is decided on it.

## Decision

Implemented in 1.2.0:
- `md-to-html`, `mermaid-render`, `marketing-flyer` and `deck-builder` are retired;
- `file-to-markdown` 0.4.0 is the rebuild, kept.
