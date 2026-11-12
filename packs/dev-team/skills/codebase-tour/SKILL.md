---
name: codebase-tour
description: Get a newcomer (a new engineer, or the agent itself) oriented in an unfamiliar repository before they make one specific change, with a short tour scoped to that change. It gives the install, run and test commands taken from CI, package scripts and the Makefile; the path the change touches, traced through the code with file:line citations; where the change goes; the conventions the code actually follows; the traps (generated files, a second copy of the logic, untested code, env vars, flags); and a first step that can be checked. Use when someone says "I'm new to this repo", "get me oriented", "where would I make this change", "walk me through the code for X", "onboard me before I start this ticket", or "how do I run and test this".
---

# codebase-tour

Orients someone in a repository they have never seen, for **one change they are about to make**. The tour is not a map of the system. It follows the path the change will touch, and it ends at the file and function where the work starts.

Two failures make a plain orientation worse than none. The first is a **confident wrong command**: `make dev` copied from a README into a repo whose Makefile has no `dev` target. The second is the **trap nobody mentions**: the generated file someone hand-edits, the second copy of the logic that stays unchanged, the test suite that skips the area. This skill is built around two rules. **Every claim cites the file and line it was read from. The README gives leads to check; the code gives the facts.**

Boundaries: a full as-is architecture write-up is `reverse-architecture`. A diagram is `interactive-diagram` or `architecture-diagrams`. A standing agent-policy file for the repo is `agents-md-generator`. Writing the change itself is `feature-implement-loop`, which takes this tour's "where the change goes" and first step as its input. Reviewing the finished diff is `pre-merge-review`.

## How to respond

**Four rules come before the steps and outrank them:**

- **Answer what was asked, first.** Open the reply with the 3–5 things this person most needs to know for this change. A directory listing is never first.
- **Use only what you read.** Every statement carries `path:line` (or a path, for a whole file) from this repository. Anything not checked is tagged `[inferred]` with the reason. A fact the repo doesn't give goes under "Open questions". It is not filled in from what the framework usually does.
- **Deliver from what you have.** Read the repo, state any assumption in one line, and produce the tour. Ask nothing when the repo and the change are both in hand.
- **Write for someone who has never heard of this skill.** No skill names, no paths or scripts from this folder, no internal terms, and nothing about how the run was set up. A next step is one plain sentence at the end.
- **For this skill:** where the README and the code disagree, say so in one line with both citations, and follow the code.

1. **Pin the change in code terms.** Restate it in one sentence using the words the code will use. ✅ *"Reject `POST /orders/{order_id}/refunds` when the event ended more than 14 days ago."* ❌ *"Tighten up refunds."* If no change is named, tour the main path from the primary entry point, tag that scope `[assumption]`, and replace "Where the change goes" with one line asking for the change.

2. **Inventory what the repo says about itself.** Run the fact lister. It is read-only: it prints commands, test files, generated-file markers, env reads and README claims that don't resolve, each with `path:line`.

   ```bash
   # Claude Code
   python3 "${CLAUDE_SKILL_DIR}/scripts/repo_facts.py" <repo-root>
   # Other IDEs (from the skill folder)
   python3 scripts/repo_facts.py <repo-root>
   ```

   If no script can run, read these by hand in order: CI workflows (`.github/workflows/`, `.gitlab-ci.yml`), then package scripts, `Makefile`, `justfile`, `tox.ini`, `noxfile.py` and `pyproject.toml`, then `README` and `CONTRIBUTING`. CI ranks first because its commands are the ones that have to pass.

3. **Take commands only from those files, and say which ones ran.** Quote each command with its source. ✅ `make test` (`.github/workflows/ci.yml:21`, which runs `pytest -q -m "not e2e"` per `Makefile:8`). ❌ `make dev` (named in the README; the Makefile has no `dev` target). Prefer CI's form of a command over the script's bare form, and list anything CI needs that a laptop lacks (a database service, an env var set in the workflow). Give each command one status:
   - `ran: passed` or `ran: failed` with the first error line. Run only commands that stay inside the repo: tests, lint, typecheck or build, and only when the toolchain and dependencies are already installed.
   - `read, not run` for everything else. That covers dependency installs, anything that needs a database, a network service or credentials, deploys, migrations, publishing, and generators that rewrite tracked files. Run these only when the user asks.

   A command to run one test file or one test is **derived**. It goes through the repo's own script or runner, plus that runner's filter argument, and it is labelled `derived from <source>`. ✅ `pytest -q -m "not e2e" tests/rules/test_refunds.py` (derived from `Makefile:8`). ❌ `python -m unittest` in a repo that runs pytest. A runner the repo never calls is invented. Leave it out.

4. **Trace the path the change touches.** Search for the change's nouns: the route string, the CLI flag, the field or column name, the error code. Work outward to the entry point (`main`, the server bootstrap, the console script, the job scheduler). Then write the path forward as numbered hops. Each hop is `path:line` `function`, plus one line on what it does there. Stop at the far edge of the change, usually the database call or the outbound request. Keep it to 10 hops or fewer. A hop you couldn't trace is `[inferred]`, with what you'd need to confirm it.

5. **Say where the change goes, and why there.** Name the files and functions. Justify each one with the pattern its nearest sibling already follows. ✅ *"Every other refund rule lives in `check_refundable` (`tallyhall/rules/refunds.py:9`), which the route calls at `tallyhall/api/refunds.py:22`. The window check goes in `check_refundable` too."* List **everything that has to change together**: a spec and the types generated from it, a registry the new code must be added to, a second copy of the logic.

6. **Read the conventions from the code nearest the change, not from the README.** Cover naming, how errors are raised and returned, test layout and naming, how config and env vars are read, and logging, but only the ones this change will hit. Each gets a citation from code. ✅ *"Errors: raise `RefundRejected(code, message)`; the route turns it into a 422 (`tallyhall/rules/refunds.py:4`, `tallyhall/api/refunds.py:25`)."* Where a file on the path breaks its own convention, say so. That file is the one a newcomer copies by mistake. Every README or `CONTRIBUTING` claim the code contradicts (a command, a path, where config lives, how a plugin is registered) goes under "Where the README is wrong", with both citations.

7. **Hunt the traps.** Check each one and report what you found. Write "none found" when a check comes up empty, so the person knows it was done.
   - **Generated files**: the marker line, the source they come from, the command that regenerates them, and whether CI checks for drift.
   - **Duplicated logic**: search for the change's identifiers, SQL, literals and constants outside the main path. A second copy is either updated in the same change or left alone on purpose, and the tour says which is the open question.
   - **Untested code on the path**: name each function on the path that no test calls.
   - **Tests the default command skips**: markers (`-m "not slow"`), build tags, include globs.
   - **Env vars and feature flags the path reads**: the name, the default, and the line that reads it.
   - **Vendored code** on the path, and where it comes from upstream.

8. **Find the tests for the area, and how to run just those.** Name the test files that exercise the path, the command for the whole suite, and the derived command for only these files. When the area has no tests, say so plainly: ✅ *"Nothing tests `tallyhall/admin/bulk_refund.py`. The first step adds one."*

9. **Name the first step: small, local, and verifiable.** It says what to do in which file, the command to run, and the result that shows it worked. A failing test next to an existing one is the usual best first step. ✅ *"Add `test_rejects_refund_after_window` to `tests/rules/test_refunds.py`, with an order whose event ended 15 days ago; run `pytest -q -m "not e2e" tests/rules/test_refunds.py`; it fails until `check_refundable` checks the window."*

10. **List open questions for a maintainer.** Five at most. Each one can be answered in a sentence and points at the evidence that raised it. ✅ *"Should the support bulk-refund tool (`tallyhall/admin/bulk_refund.py:27`) apply the 14-day window too, or is it the override?"*

11. **Write it with [`templates/codebase-tour.md`](templates/codebase-tour.md), under the caps.** The whole tour is ≤ ~120 lines and each section is ≤ ~15 lines, about one screen. The scope line names what was **deliberately skipped**: the areas not on the path, the services not read. That way the person knows it is a scoped tour and not a survey. If a section would overflow, cut the hops and conventions furthest from the change first.

12. **Reply.** Lead with the 3–5 bullets, then the tour. Put the tour in the reply. Write it to a file only when the user names a path, and change nothing else in the repository.

**Non-interactive runs** (subagent, CI, headless): an unnamed change becomes a main-path tour tagged `[assumption]` (step 1). Unclear scope boundaries become `[assumption]` lines at the top. A repository that cannot be read emits `BLOCKED: need read access to the repository — every claim in the tour cites a file in it`, followed by one plain sentence saying the tour follows once the files can be read. A tour is never written from a description of a repo.

## Useful references in this skill

- [`templates/codebase-tour.md`](templates/codebase-tour.md): the tour skeleton, with section order and line budgets
- [`scripts/repo_facts.py`](scripts/repo_facts.py): read-only, stdlib-only fact lister (commands with provenance, README commands and paths that don't resolve, tests, generated markers, env reads)
- [`examples/refund-window.md`](examples/refund-window.md): worked input → output for a Python service, including a README that disagrees with the code and a second copy of a rule

## Quality bar

- **Every claim has a citation or an `[inferred]` tag.** Run a spot check: pick any three statements in the tour, and each must lead to a file and line that says it.
- **Zero invented commands.** Every command traces to CI, a package script, a Makefile, a tox or nox session or pyproject, or it is a labelled derived filter of a runner the repo already calls.
- **Ran and read are never blurred.** Every command carries `ran: passed`, `ran: failed`, or `read, not run`.
- **README-versus-code conflicts are named**, each with both citations and the code taken as the fact.
- **Scoped, not surveyed.** The path stops at the change's far edge, the tour fits the caps, and the scope line says what was skipped.
- **The trap checks all report**, including "none found". A second copy of the logic, when one exists, is named with its location.
- **The tests for the area are named, with a command for just those**, or the tour says plainly that there are none.
- **It ends at a place to work.** Files and functions, then a first step with a command and an expected result, then at most five open questions.
- **The reply leads with the 3–5 things that matter**, not a tree.

## When to use this skill

- ✅ "I'm new to this repo and need to add X. Get me oriented."
- ✅ A ticket is picked up in an unfamiliar codebase and the first hour is going on finding where things live
- ✅ An agent is about to implement a change in a repo it has not read, and needs the commands and traps before writing code
- ✅ "How do I run and test this, and where would this change go?"
- ✅ Handing a scoped piece of work to a contractor or a new teammate with a page that is true

## When NOT to use this skill

- ❌ A full as-is architecture write-up or diagram of the whole system: `reverse-architecture`
- ❌ Drawing a diagram of a flow or a system: `interactive-diagram` or `architecture-diagrams`
- ❌ Writing a standing `AGENTS.md` or agent-policy file for the repo: `agents-md-generator`
- ❌ Writing the code for the change: `feature-implement-loop`
- ❌ Reviewing a diff that already exists: `pre-merge-review`

## Anti-patterns to avoid

- ❌ **Copying the README's commands.** A README goes stale first. Check every command it names against the scripts and CI, and report the ones that don't exist.
- ❌ **Ecosystem-default commands.** `pytest` for a repo that runs `nox -s tests`, `make test` in a repo with no Makefile. The repo says what it runs.
- ❌ **"Run the tests" without saying whether you did.** A reader can't tell a command that passed from one copied out of a file.
- ❌ **The architecture survey.** Twelve services described, and the one function the change touches never named. Follow the path; skip the rest and say so.
- ❌ **A directory tree as the opening.** The person can run `ls`. Open with what changes their next hour.
- ❌ **Conventions from the style guide.** `CONTRIBUTING.md` says "use custom error classes"; the handler on the path returns `{ error: string }`. Report what the code does, and flag the gap.
- ❌ **Missing the second copy.** The change lands in the API route, and the admin tool with its own copy of the same rule keeps the old behaviour. Search for the identifiers before naming where the change goes.
- ❌ **Editing a generated file in the first step.** Name the source and the regenerate command instead.
- ❌ **Running something with side effects to "check it works".** Deploys, migrations, installs that hit the network, and generators that rewrite tracked files stay `read, not run` unless the user asks.
- ❌ **A first step that can't be checked.** "Get familiar with the handler" is not a step. Name a file, a command and an expected result.
- ❌ **Showing the machinery.** No skill names, script names or caps in the reply or the tour.
