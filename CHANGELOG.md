# Changelog

What shipped in each released version of `skilldrop-cli`. The site reads the newest three
entries into its **Recently shipped** section (RFC-0026), and `build_site.py` refuses to
build if the version at the top of this file disagrees with `package.json` — so a release
cannot ship undocumented.

Format: `## <version> — <YYYY-MM-DD>`, newest first, one bullet per user-visible change.
Bullets say what a user can now do, not which files moved.

## 0.16.43 — 2026-10-21

- **Every skill script has unit tests:** 1,317 tests for the 48 scripts in 43 skills, run on Linux, macOS and Windows on every pull request. Every new script needs tests: `validate.py` fails a skill whose scripts have none. Run them with `python3 -m unittest discover -s tests -t .`. They use only the standard library and run offline ([RFC-0060](docs/rfcs/0060-skill-script-unit-tests.md)).
- **Two Windows bugs, found by running the tests on Windows, are fixed:**
  - `tracker-brief-sync` 0.1.1 wrote its Jira and CSV imports with a blank row between every issue;
  - `interactive-diagram` 0.2.3 crashed when the output file was on a different drive from the current folder.
- **Writing the tests found 60 bugs in 34 skills.** Each is recorded as a known failure and fixed in a follow-up release. About 25 give a wrong result, such as AWS spot compute always reported as $0, or a sprint filter that also matches a later sprint. The rest crash on input they should reject with a clear message.

## 0.16.42 — 2026-10-21

- **skilldrop's site is reviewed by its own skills**, and the [reviews are published](https://sananthanarayan.github.io/skilldrop/docs/explanation/own-skills-on-own-site.html) ([RFC-0061](docs/rfcs/0061-own-skills-on-own-site.md)).
  - **`accessibility-audit`** found three problems, now fixed:
    - keyboard focus was invisible on three of the four install tabs on the home page;
    - text on the accent colour was just under 4.5:1;
    - search-field borders were too faint to find.

    Every checked page now scores 100 on Lighthouse's accessibility checks.
  - **`web-performance-review`** found no vital at risk in the lab: LCP 1.0–1.9 s, CLS 0, no blocking time. The docs pages no longer wait on the code-colouring stylesheet before they paint.
- **Pull requests here are reviewed by `pre-merge-review`**, with the review posted to the check's summary. It reports and never blocks, and it runs only once the repository's API key is set.

## 0.16.41 — 2026-10-21

- **The share card says what sets skilldrop apart.** The card that shows when the site or repo is linked in Slack, Teams or LinkedIn says that skills are run with and without themselves, that 4 were retired for losing, and that gates can say no. `validate.py` checks the retired count on the card against the catalogue, the same way it checks the other counts.

## 0.16.40 — 2026-10-20

- **Every release can be verified.** Each GitHub Release now carries:
  - the exact tarball published to npm;
  - a Sigstore-signed build provenance for it (`gh attestation verify skilldrop-cli-<version>.tgz --repo sananthanarayan/skilldrop`);
  - a CycloneDX SBOM.

  Its notes are this changelog entry, and its title is the pull request's ([RFC-0059](docs/rfcs/0059-signed-releases-and-scorecard.md)).
- **The repo is scored by [OpenSSF Scorecard](https://scorecard.dev/viewer/?uri=github.com/sananthanarayan/skilldrop)** every week and after every merge, with a badge on the README.
  - CI's own tools now install from hash-locked files.
  - Every workflow is read-only at the top level.
- **The README leads with the evidence:**
  - one real request answered with and without a skill, and the blind judge's verdict;
  - the last run's numbers;
  - the skills that were retired for losing.
- **The CLI asks for a GitHub star once.** The line prints after your first successful install, at an interactive terminal only, never in CI, a pipe or `--json`. Set `SKILLDROP_NO_STAR=1` to turn it off. Nothing is sent anywhere.

## 0.16.39 — 2026-10-20

- **Eval fixtures no longer raise Dependabot alerts.** A fixture's fake `package.json`, `go.mod`, `pyproject.toml` or CI workflow is now stored as `<name>.fixture`. GitHub no longer reads its pins as the repo's own dependencies, which had produced 33 alerts and six security PRs against code nothing installs or runs. `run_bench.py` gives each file its real name in the run's workspace, and `validate.py` fails on a fixture dependency file that keeps its real name ([RFC-0058](docs/rfcs/0058-fixture-dependency-files.md)).

## 0.16.38 — 2026-10-20

- **A [Get started](https://sananthanarayan.github.io/skilldrop/start/) page** takes a newcomer through four steps:
  - install with the CLI, the Claude Code plugin or a copied folder;
  - choose the work in front of you, with the install command and a first prompt for each choice;
  - make the first request in plain words;
  - check the verdict and where you decide.

  It is first in the site's navigation and on the home page.
- **The packs page opens with "Start with your role"**: thirteen roles, each pointing to its packs. Every pack must be placed under a role, so the site build fails if a new pack is missing from the list.
- **The docs have a copy button on every code block.**
- **Each kind of guide has an index page.** Tutorials, how-tos, reference and explanation each list their guides, and the kind in a guide's header links back to that list.
- **Each tutorial card says how long the tutorial takes,** where the tutorial itself says so.
- **The contributing guide is in the docs**, published from `CONTRIBUTING.md` so the two can't disagree.
- **A pack page shows how long a session takes** beside the pack's size, when the pack's journey says so.

## 0.16.37 — 2026-10-20

- **`bundle-size-review`**, in the `frontend` pack, finds what makes a JavaScript bundle heavy from webpack, esbuild or Vite stats. Before reaching a conclusion, it reads your repository: the browser targets, the bundler config, the installed versions, and the files that import each heavy package. It reports exact byte sizes for what each entry loads before first render, the import chain behind each heavy module, duplicates, and polyfills your browser targets don't need. Given before and after stats, it shows what grew and which per-entry budget would have caught it.
- **`judge-audit`**, in `ai-engineering`, checks whether an LLM judge can be trusted for the decision its scores drive. It measures agreement with expert labels, using weighted kappa for 1–5 scores. Its numbers are broken down by the variants you're comparing, so a judge that favours one of them shows up. Each run is reported separately, a rare class gets precision and recall with intervals, and the result is checked against your own pass mark.
- Both failed their first measurement in 0.16.36. They were revised from the judges' reasons, then preferred to plain Claude Code on new held-out evals ([RFC-0057](docs/rfcs/0057-standing-out-and-closing-gaps.md)).

## 0.16.36 — 2026-10-20

- **Ten new skills.** Each was preferred by blind judges to plain Claude Code on held-out evals ([RFC-0057](docs/rfcs/0057-standing-out-and-closing-gaps.md)).
  - **`behaviour-equivalence`** proves that a rewrite or migration behaves like the old code. It records the old system first and runs it twice to see what varies on its own, normalises one field at a time with a reason, and makes you classify every remaining difference. Its script does the diff.
  - **`event-contract-draft`** writes an AsyncAPI 3.0 event or message contract: event names, an id for deduplication, the partition key and the ordering it does and doesn't give, idempotent consumers, minimal personal data, and safe versioning. `api-contract-draft` now hands event contracts to it.
  - **`slo-spec`** writes SLOs from your user journeys. Its script turns the error budget into minutes and bad requests and works out burn-rate paging alerts, and it checks each target against what your dependencies allow.
  - **`lean-canvas`** finds what could kill an idea: every box tagged as evidence or assumption, the riskiest assumption first with the cheapest test to disprove it, and the unit economics computed.
  - **`agent-config-review`** checks a Claude Code, Codex or Cursor setup for more access than the work needs, reading every settings scope plus hooks, MCP servers and subagents, and gives the exact config to replace each problem.
  - **`agent-incident-response`** covers the first hour after an agent leaks a key, deletes something or runs up a bill. It answers your question first, revokes the key before anyone touches git, and gives exact recovery steps.
  - **A new `frontend` pack:**
    - **`web-performance-review`** reads a Lighthouse or PageSpeed Insights report for what slows the page for real users, ranked by how much each fix moves the failing Core Web Vital.
    - **`rendering-strategy`** decides, route by route, whether each page is static, revalidated, server-rendered or client-rendered.
  - **`md-to-pptx`** turns Markdown into PowerPoint with nothing to install. Long sections split onto "continued" slides, and the reply names any speaker note that would go out with the file.
  - **`md-to-confluence`** turns Markdown into a Confluence page, and publishes it only after showing which page and version it will overwrite.
- **A `modernize` loop** for replacing legacy code. It records the old component's behaviour before anything is rebuilt, a script compares the new one against those recordings (G10), and a person decides the cutover (G10.1).
- **`file-to-markdown` reads email:** `.eml`, and Outlook `.msg` with nothing to install. You get the subject, sender, recipients, sent time and body, with attachments listed by name and size.
- **Three new review agents:**
  - **`test-reviewer`:** would these tests catch the bug?
  - **`docs-reviewer`:** do the docs still match the change?
  - **`finding-adjudicator`:** checks a review panel's findings against the code and returns one ranked list.

## 0.16.35 — 2026-10-20

- **`file-to-markdown` keeps PDF table columns apart when they sit close together.** A right-aligned amount next to a left-aligned date used to merge into one cell ("1,137 2027-02-01"), because the PDF's text puts only one space between them. Columns are now told apart by where each word sits on the page, and a normal word space never splits a cell, even in a monospace font. A table that already came out right is unchanged. On a 60-row table exported from Word, every row now has its four columns.

## 0.16.34 — 2026-10-20

- **`skilldrop search <words>`** finds skills, loops, agents and packs by what they're for, from the terminal and offline. It reads names, tags, packs, descriptions and the phrasings each skill's trigger evals route to it, so `skilldrop search why did our conversion drop` finds `hypothesis-comparison`. Every word must match, filler words are dropped, and if nothing matches every word it shows near matches and says so. Search a retired skill by name and you get its retirement note. `--kind`, `--limit` and `--json` refine it ([RFC-0056](docs/rfcs/0056-search-and-windows-ci.md)).
- **The CLI is tested on Windows, macOS and Linux** on every pull request: installs into folders and git repos, `--project`, `--local`, agents, loops, containment, policies, mirrors and a skill's own Python script. Every check passed on Windows the first time.
- **Fixed for Windows:**
  - **Five skills' scripts could fail on Windows.** They read files with Windows' default encoding and stopped at the first non-ASCII character. They now read and write UTF-8: `brand-kit`, `marketing-flyer`, `deck-builder`, `ai-usage-report` and `pre-merge-review`. Run `skilldrop update` to get the fix.
  - **`validate.py` now runs on Windows**, so contributors can lint a clone there, and it rejects any script that reads text without an encoding.

## 0.16.33 — 2026-10-20

- **Eval results now build a history.** The evals workflow runs the trigger queries every week and, from this release, the acceptance assertions every month under a dollar budget ($20 unless you set `EVALS_MONTHLY_BUDGET`). Each run's counts are appended to an `eval-history` branch, and the *How skills are checked* page draws them week by week: trigger accuracy over time, the skills whose routing changed since the last run, and what each monthly run graded and spent. It starts once the repository has an `ANTHROPIC_API_KEY` secret ([RFC-0055](docs/rfcs/0055-eval-history-branch.md)).
- **`run_evals.py --budget`** stops starting new calls once the dollar cap is reached, and `--summary` writes the counts-only file the history keeps.
- **`file-to-markdown` reads scanned PDFs** when `tesseract` is installed. Each page with no text layer is read by OCR (`--ocr-lang` for other languages), and the reply says which pages were OCR'd so you check their numbers and names. A table that runs onto the next page now comes out as one table, without the header the PDF repeats, and a paragraph after a table is no longer pulled into it.
- **The converters' output checked in real Office.** Word for Mac 16.114 opens the `md-to-docx` example with no repair prompt and keeps its headings, table, image and links in its own PDF export. Excel 16.114 reads the `md-to-xlsx` example's amounts, percentages, dates and TRUE/FALSE as real values, with filters on and the header frozen.

## 0.16.32 — 2026-10-20

- **A skill's instructions are now held to its `permissions`.** A skill without scripts can still tell your agent to run `terraform init` or `curl` a host. The scan now reads every fenced shell block in a skill's instructions, and `skilldrop validate` fails one that runs a program or reaches a host it doesn't declare. `--contain` lets shell commands reach only the declared hosts, so they now include the ones instructions need. Six bundled skills declare what their instructions run: `sonar-review`, `terraform-module`, `terraform-plan-review`, `mermaid-render`, `figma-diagrams` and `dependency-upgrade-review` ([RFC-0054](docs/rfcs/0054-instruction-permissions-and-agent-scan.md)).
- **`skilldrop scan` checks agents too.** It applies the same rules it uses on skills, plus four of its own:
  - an agent with no `tools:` list, which inherits every tool;
  - one that reads from the web or an MCP server and can run commands or edit files in the same context;
  - a permission mode that skips your approval;
  - hooks in its frontmatter.

  `scan --agent` scans agents only. Installing agents from a third-party catalogue shows the findings, and a policy's `scan.max` now refuses agents above its limit too.
- **`dependency-upgrade-review` leads with the verdict and what decides it.** Each blocker says what breaks, where, why CI missed it, and how to fix it. The review now traces changed APIs to their callers, checks runtime floors against the image and CI, and flags one tag pinned to two SHAs. On new held-out evals, both judges preferred it to plain Claude Code in every pair ([RFC-0053](docs/rfcs/0053-six-skills-for-the-lifecycle-gaps.md)).

## 0.16.31 — 2026-10-20

- **`rollout-plan`** plans turning on a flagged or canaried change. It answers your question first, then builds the ramp around what actually limits it: a partner's daily cap, a billing cycle, a shadow run, or traffic too low for percentages to mean anything. Each step has a threshold measured against the flag-off group and a rule set in advance, and the plan says how long the step must run to catch a regression and what turning the flag off doesn't undo. It's an option in the `release` loop's first stage, beside `migration-plan`.
- **`refactor-plan`** plans paying down one piece of technical debt in small steps, each its own PR, with main releasable after every one. Characterisation tests go first on the code that has caused incidents. Each step is labelled refactor or behaviour change, and the plan ends at the structure your goal needs. A question asked in chat gets a plan sized for chat.
- Both failed their first measurement in 0.16.30, were revised from the judges' reasons, and were then preferred to plain Claude Code in every pair on new held-out evals ([RFC-0053](docs/rfcs/0053-six-skills-for-the-lifecycle-gaps.md)).

## 0.16.30 — 2026-10-20

- **Four new skills**, each admitted on held-out evals written by someone who saw only its description ([RFC-0053](docs/rfcs/0053-six-skills-for-the-lifecycle-gaps.md)):
  - **`dependency-upgrade-review`** gives a merge verdict on a Dependabot or Renovate pull request: MERGE, MERGE AFTER CHECKS or DO NOT MERGE. It reads the release notes for every skipped version and lists what the lockfile changes beyond the title. Each SHA pin stays unverified until it matches its tag. It says whether CI ran the changed code and writes the rollback.
  - **`feedback-synthesis`** turns tickets, NPS comments, reviews and interview notes into ranked problems. Each one is counted by distinct people, not mentions, with verbatim quotes and what the sample can't tell you. It's an option in the `discover` loop's first stage.
  - **`codebase-tour`** orients someone in an unfamiliar repo before one change. Commands come from CI and the package scripts. The path the change touches is cited to file and line, and the tour flags where the README is wrong and what traps to avoid. It's an option in the `build` loop's first stage.
  - **`mcp-pairing`** says which MCP servers a loop needs, stage by stage, with the narrowest access: read-only by default and never write access on a review or gate stage. It names no server you didn't, and gives a fallback for running without one.
- **`loop-stats` combines a team's numbers and draws them.** Pass several run logs, or other people's `--json` summaries, and it shows them as one view. `--html` writes a dashboard of each gate's verdicts, overall and week by week, that loads nothing from the network. The `--json` summary no longer includes the log's file path, so it can be shared ([how-to](guides/how-to/measure-your-loops.md)).
- **Compare two packs** side by side on the site, from the packs page or any pack's page: what each is for, its loops and where a person decides, and the skills only one has.
- **A how-to for every skill** in the docs: install it, requests that route to it, what a good result looks like, what to use instead, and which loops run it. There are now 191 guides.

## 0.16.29 — 2026-10-20

- **Three new loops, for jobs that run alongside delivery** ([RFC-0052](docs/rfcs/0052-research-comply-measure-loops.md)):
  - **`research`** takes a question about why something happened to an answer the evidence can carry. The plan fixes what would change the decision before any source is read. Its gate (G7) passes only when the evidence separates the leading explanation from the runner-up; otherwise it sends the work back for the one observation that would. `npx skilldrop-cli install --loop research`.
  - **`comply`** takes a risky change (a launch, a vendor, new personal data) to a risk position its owner signs. The DPIA's risks to people join the register. A control the evidence map can't evidence gives a rating no credit. The register's own script decides G8, and only the named owner signs at G8.1.
  - **`measure`** takes a dashboard request to numbers people can defend. The spec cuts charts before any SQL is read. A query that fails review goes back through the spec, because the fix moves the number. Each metric's owner confirms its definition at G9.1, and an undefined metric is never filled in for them.
- **A hand-written tutorial for each pack added in 0.14.0**, each worked on one example from start to finish, with output from real runs: [converters](guides/tutorial/one-draft-every-format.md), [experience-design](guides/tutorial/page-to-service.md), [research](guides/tutorial/why-question-to-evidence.md), [trackers](guides/tutorial/prd-to-honest-tracker.md), [data-analytics](guides/tutorial/dashboard-request-to-defensible-numbers.md), [grc](guides/tutorial/risky-change-to-signed-risk.md), [infra-as-code](guides/tutorial/module-to-safe-apply.md) and [skill-engineering](guides/tutorial/write-and-review-a-skill.md).

## 0.16.28 — 2026-10-19

- **Contain what a skill can reach.** `skilldrop install <skill> --project --contain` turns on Claude Code's strict sandbox for that project, sized to what the skills declare: shell commands, and everything they start, write only inside the project and reach only the hosts the skills say they need. It only ever tightens your settings, never loosens or widens them, keeps the file out of git, and refuses a skill that says it writes anywhere on disk. It also says plainly what the sandbox doesn't cover (Claude Code's file and web tools, MCP servers, hooks) and how to close that ([RFC-0051](docs/rfcs/0051-declared-containment.md), [how-to](guides/how-to/contain-skills.md)).
- **A policy can require it.** With `"require_containment": true`, an install that isn't contained is refused, and Claude Code won't start in a contained project if its sandbox can't. `skilldrop inventory` shows which projects are contained.

## 0.16.27 — 2026-10-19

- **An organisation can decide what its people install.** Hand out a policy file (`--policy`, `SKILLDROP_POLICY`, or `~/.config/skilldrop/policy.json`) and the installer enforces it: only the catalogues you allow, pinned to a commit if you say so, only the skills you allow, none you block, and nothing whose supply-chain scan finds worse than you accept. A refused install writes nothing and names the rule; `update` leaves refused skills as they are. A policy with a mistake stops the command rather than being half-applied ([RFC-0050](docs/rfcs/0050-org-governance.md), [how-to](guides/how-to/govern-skills.md)).
- **`skilldrop inventory` lists every install on a machine**, across every tool and scope, with what the policy thinks of each; `--merge` combines reports from many machines into one view. Paths under your home directory are written as `~`.
- **An audit log that shows if it was edited.** With `audit` in the policy, every install, update and uninstall is recorded; each line carries the fingerprint of the one before, and `skilldrop audit verify` names the first line that doesn't follow. Entries name a pseudonym only your organisation can resolve, unless it chooses otherwise.
- **`skilldrop verify-mirror` checks an internal mirror** against the fingerprints `skilldrop package` recorded, and names every file changed, missing or added since.

## 0.16.26 — 2026-10-19

- **`interactive-diagram` asks for what a reader needs from the reply:** the link and the takeaway at the top, with at most one short line about the build before them. Three attempts to remove that line changed little, and a reader who has just watched the build run loses nothing to it ([RFC-0048](docs/rfcs/0048-interactive-diagram.md)).

## 0.16.25 — 2026-10-19

- **The site shows live examples as a gallery.** The home page and each skill page with finished example pages show them as cards with a live, shrunken preview of the real page, which opens full size when clicked. The previews run in a sandbox with no access to the site and load only when scrolled to.
- **`interactive-diagram` pages work inside a sandboxed frame** (an embed, or the site's preview), where the browser refuses saved preferences; the theme simply follows the system setting there.
- **`interactive-diagram` has two more evals written by someone who never read the skill**, a repository's data flow and a process told in words; two blind judges preferred it to plain Claude Code in 4 and 3 of 4 pairs. A reply drafted by the script, tried to make replies open with the link, did not, and was reverted ([RFC-0048](docs/rfcs/0048-interactive-diagram.md)).

## 0.16.24 — 2026-10-19

- **Commits and content can't publish a maintainer's own identity by accident.** `python3 privacy.py` reads who you are from your own machine (the signed-in Claude account, git config, your user name and home directory, plus anything you list in the git-ignored `.skilldrop-private`) and stops your name, email, organization or home path reaching a commit, a commit message or any tracked file, without ever printing them. Turn the hooks on once per clone with `git config core.hooksPath .githooks`; `validate.py` runs the same scan. CI now fails a push or pull request whose commits use anything but a GitHub noreply email, for every account that commits ([RFC-0049](docs/rfcs/0049-identity-guard.md), [SECURITY.md](SECURITY.md#keeping-your-identity-out)).
- **Benchmark runs say when an output named you.** A model will write the signed-in account's name into an Author field unasked (it did three times in the tier run, once with no skill at all). `run_bench.py` now counts those runs in the report, replaces the name with [you] in `results.json`, and refuses to publish a summary that contains it.
- **`design-doc` fills its Author field only from your brief**, and leaves it blank otherwise.
- **The benchmark guide shows how to run a long benchmark from a terminal**, detached, so a task time limit can't stop it halfway; a rerun resumes from the cache.

## 0.16.23 — 2026-10-19

- **`interactive-diagram` draws four more kinds of diagram:** class diagrams from source (members, interfaces and abstract classes, and inherits, implements, composition, aggregation, association and dependency), trees of what contains what, timelines of an incident or a release, and waterfalls of where the time went in one request or run. A timeline puts sources from different time zones on one clock, marks approximate times, and shortens a long quiet stretch so a burst of events stays readable. A waterfall marks the critical path and gives each span's own time.
- **It works out what a trace or timeline shows, and says it at the top of the page:** what the whole waited on, which steps only wait on their children, which steps ran side by side (with the real elapsed time, not the sum), what ran on after its parent, and the longest quiet stretch. Your own guesses ("is it the north fetch?") can be answered in a table at the top, each with its evidence. Durations read as you'd say them (9m 48s, not 588000 ms).
- **A long flow wraps onto rows** instead of shrinking to fit, so a 14-step process stays readable on a laptop.
- **The detail panel's "what it depends on" and "what depends on it" buttons were swapped**; they now say what they do, in each diagram's own terms ("Everything inside it" on a tree, "What led to it" on a timeline).
- **Two more live examples** on the skill page: an incident timeline and a slow request's waterfall, both built from files whose every cited line was checked.
- On two new evals written by someone who never read the skill, two blind judges preferred it to plain Claude Code in 4 and 2 of 4 pairs, with 81% of checks met against 44% ([RFC-0048](docs/rfcs/0048-interactive-diagram.md)).

## 0.16.22 — 2026-10-18

- **New skill: `interactive-diagram`** (`solution-architect`). Ask for an interactive diagram of a repo, a request path, a process or a schema and get one HTML file you can send: architecture, data flow, workflow, lifecycle, ERD or sequence. Every box and arrow cites the file and lines or the words it came from, and anything the material doesn't show is drawn dashed as an assumption. Each cited line is checked against the repository before the page is written, and clicking a part shows the cited code. Nobody places anything by hand: the script lays the diagram out with no arrow crossing a box. The page works offline, loads nothing from the network (its security policy blocks it), and offers pan and zoom, paths between parts, what depends on what, a walkthrough, light and dark, and SVG, PNG and Mermaid export. It can also compare two versions and mark what was added, removed and changed. It needs only Python 3. On two evals written by someone who never read the skill, two blind judges preferred it to plain Claude Code in 4 and 3 of 4 pairs ([RFC-0048](docs/rfcs/0048-interactive-diagram.md)).
- **Skill pages can show live examples.** A finished page in a skill's `examples/` folder is published beside the skill's page on the site; `interactive-diagram` has two.
- **`skilldrop scan` lists what it finds in a worked example's input files** (`examples/inputs/`) without raising it, as it already does for eval fixtures. The skill never runs either.

## 0.16.21 — 2026-10-18

- **`role-shortlist` handles a few pasted blurbs and "just the top two".** It answers with the picks and a line or two on the rest, with no empty "Not read" or "Closed or duplicate" groups, and an item a posting calls preferred, desirable or a plus no longer rules a role out. On two new evals written by someone who never read the skill, two blind judges preferred it to plain Claude Code in 3 and 2 of 4 pairs, up from 3 and 1 ([RFC-0047](docs/rfcs/0047-role-shortlist.md)).
- **The light and heavy tiers resolve to Claude Haiku 5.5 and Claude Opus 5.5** in Claude Code, up from Haiku 4.5 and Opus 5, so the `model-router` agent and `route.py` pick the current models.
- **The benchmark has run on the light and heavy tiers.** On the 224 held-out evals, a skill on Haiku 5.5 meets 83% of its checks and on Opus 5.5 85%, at about a twenty-seventh of the cost; light came within 5 points of heavy for 61 of 97 skills, including 9 of the 13 assigned heavy. Blind, the plain agent was preferred on both tiers: the skill won 41% and 48% of pairs on Haiku 5.5, and 31% with both judges on Opus 5.5. No tier was changed; the account is in [What the benchmark showed](guides/explanation/what-the-benchmark-showed.md#the-light-and-heavy-tiers) and the summary in `docs/benchmarks/tiers.json`.
- **`run_bench.py` prices a model Claude Code has no price for yet** from its own table, instead of the placeholder rate Claude Code reports, so a new model's dollars per run are list price.

## 0.16.20 — 2026-10-18

- **New skill: `role-shortlist`** (`career`). Give it an employer's careers page saved as files, a job-board export or a folder of postings, plus your resume, and it says which roles to apply for. Each role is judged only from its own posting text; one it could not read is listed as unread, never ranked from its title; an unmet licence, registration, location or required degree takes a role out whatever else fits; the same role posted twice counts once; every role you gave appears once. Admitted on a measured result ([RFC-0047](docs/rfcs/0047-role-shortlist.md)): on two evals written by someone who never read the skill, two blind judges preferred it to plain Claude Code in 3 of 4 pairs each.
- **Every skill now has held-out evals.** 84 skills gained two evals each, written by agents that read only the skill's one-line description, so every skill in the catalogue now has checks it was never revised against: 224 of the 376 evals. `run_bench.py --held-out` runs only those, and its report and the published summary split every number into evals the author wrote and evals written without seeing the skill. The site's home page and evals page show the split once a run is published.
- **Installs no longer copy a skill's `evals/` folder.** The evals are how the catalogue measures a skill, not something the agent reads, and some fixtures are bait on purpose (a script that reads credentials, for a reviewer to catch). `outdated`, `update` and `diff` ignore them too, so adding evals is not a change to the skill. `skilldrop scan` still lists patterns found inside eval fixtures, marked as fixtures the skill never runs.
- **`job-fit-analysis` points to `role-shortlist`** for a long list of openings and keeps the two-or-three-posting case.

## 0.16.19 — 2026-10-17

- **`devils-advocate` says what your tests actually prove.** For every passing test or clean local run you cite, it says whether it could have caught each bug it found, and if not, why it passed (a fixture that dodges the bug, an empty local table, one run where the bug needs two) and which test would fail today. It traces each finding through the code before reporting it, so a parameterised query isn't flagged as injection. It gives fixes as code when they're small, and keeps to the scope you ask for ("top 3", "skip the nits"). The four-lens sections, severity counts, verdict labels and the mandatory "what's solid" section are gone. On two evals it had never seen, two blind judges preferred it to plain Claude Code in 4 and 2 of 4 pairs, up from 2 and 1 ([RFC-0046](docs/rfcs/0046-keep-rebuild-or-retire.md)).
- **The `devils-advocate` subagent follows the same rule**, and still tags findings blocker, major, minor or nit when a merge gate such as `pre-merge-review` needs them.
- **The rebuilds in RFC-0046 are done.** Six skills were rebuilt around the one rule each adds and shipped, and `design-doc` stayed as it was. On evals they had never seen, the six went from 10 and 11 of 24 pairs to 19.5 and 18; counting `design-doc` too, 12 and 13 of 32 became 21.5 and 20.

## 0.16.18 — 2026-10-17

- **`guide-builder` writes a guide that holds only what your notes say**, at the length its reader needs: a README section, a sheet for volunteers, a page for a new starter, or a reference for developers. Anything it infers from the notes (a unit from a sample value, what a field probably means) is marked where it appears. Steps are ordered so nothing is used before it is set up. Questions for you stay in the reply, so the guide can be sent as it stands, and where the notes leave a gap the guide tells the reader who to ask. The three fixed templates and the "reading this as a setup guide" opener are gone. On two evals it had never seen, two blind judges preferred it to plain Claude Code in 3.5 and 4 of 4 pairs, up from 2 and 3 ([RFC-0046](docs/rfcs/0046-keep-rebuild-or-retire.md)).

## 0.16.17 — 2026-10-17

- **`ai-usage-policy` writes the policy your staff will actually follow, at the length they need**: a note for a dozen staff to pin up, a page to attach for a client, or the full policy. It says what's allowed first, pairs every "don't" with what to do instead (or says no approved way exists yet and who decides), and says what to do if data has already gone into a tool. It makes no claim about a tool's data handling, seats, owners, turnarounds or laws you didn't give it, and reports a vendor's assurances as the vendor's. The fixed three-tier table, review matrix and owner-per-section are gone. On two evals it had never seen, two blind judges preferred it to plain Claude Code in 3 and 2 of 4 pairs, up from 0 and 1 ([RFC-0046](docs/rfcs/0046-keep-rebuild-or-retire.md)).
- **`design-doc` stays as it was.** A rebuild matched it on two new evals without beating it, so it was not released. The two new evals ship with the skill.
- **`run_bench.py` no longer rejects a correct judge verdict** when Claude Code's small side calls on a lighter model produce more output tokens than the verdict itself.

## 0.16.16 — 2026-10-17

- **`postmortem-generator` writes the postmortem at the length and for the reader you name**: half a page for a board, a note for customers, or the full incident review. It still never names a person as the cause, even when your notes do. It now says plainly who or what noticed first and how long before any alert, keeps what is known apart from what is still open, gives owners and dates only where your material does, and leaves no `[missing]` fields or empty template rows in the document. Runbook edits are included when the incident showed a procedure was wrong. On two evals it had never seen, two blind judges preferred it to plain Claude Code in 2 and 3 of 4 pairs, the same as before the rebuild, and a run costs less than half as much. It still loses on a short note for a very small team ([RFC-0046](docs/rfcs/0046-keep-rebuild-or-retire.md)).

## 0.16.15 — 2026-10-17

- **`release-notes` writes one set of notes for the reader and channel you name**: a changelog page, a member email, an in-app "what's new" with a word limit, store text, or your repo's own `CHANGELOG.md` style. It says nothing the log or your notes don't, keeps a vague change as vague as you described it, leaves out work reverted later in the range, and finds a breaking change from the message text as well as from `!:` markers, phrasing the action for how your readers get the release. The commit range, counts, hashes and review lists no longer appear in customer text; what it left out is listed once, after the notes. On two evals it had never seen, two blind judges preferred it to plain Claude Code in all 4 pairs each, up from 3 and 3, at a lower cost per run ([RFC-0046](docs/rfcs/0046-keep-rebuild-or-retire.md)).
- **The `release` loop's announce stage** now drafts notes for each audience you name, instead of always a customer and an internal version. Loop version 0.3.1; `npx skilldrop-cli update` takes it.

## 0.16.14 — 2026-10-17

- **`source-synthesis` answers your question from your sources, in the size you asked for.** It says only what the material supports and marks anything from elsewhere in the sentence where it appears. It counts a source that repeats another once, adds up each source's own totals and says which don't match, and gives a labelled estimate with its range when you need a figure the sources don't settle. Page-level citations, strength ratings and the citation checker are kept for when you ask for a literature review. On two evals written after the rebuild was planned, two blind judges preferred it to plain Claude Code in 3 of 4 pairs each, up from 1 and 0, at half the cost per run ([RFC-0046](docs/rfcs/0046-keep-rebuild-or-retire.md)).
- **`run_bench.py --evals 6,7` runs only the evals you name**, so a revision can be measured on the evals it has never seen without paying to rerun the rest.

## 0.16.13 — 2026-10-17

- **Four skills are retired: `tech-comparison-matrix`, `db-schema-design`, `metric-definition` and `contribution-wizard`.** On evals they were never revised against, the agent without them did as well or better, and none adds a rule the agent breaks on its own, only a format it can produce when asked ([RFC-0046](docs/rfcs/0046-keep-rebuild-or-retire.md)). An installed copy keeps working. The catalogue now holds 96 skills.
- **The CLI says when a skill you installed was retired.** `outdated`, `update` and `doctor` name it with the reason and the `uninstall` command, and remove nothing. `install`, `info` and `diff` on a retired name stop with the same reason instead of "unknown skill". The evals page lists every retired skill and why.
- **`tool-use-schema-writer` gives the tool definition you asked for**, and adds the Python `client.messages.create` snippet only when you ask for it.
- **Sixteen skills that pointed at a retired one were updated** so their hand-offs and "when not to use" lines no longer name a skill that is gone. The `data-analytics` pack now starts with `sql-review`, then `dashboard-spec`, then `doc-critique`.
- **Seven more skills will be rebuilt around the one rule each adds**, one at a time, and each ships only if two blind judges prefer it on evals it has never seen. The [roadmap](ROADMAP.md) lists them.

## 0.16.12 — 2026-10-16

- **The site has a dark theme.** It follows your system setting, and the new toggle in the nav switches it and remembers your choice. The operating-model picture has a dark version too, on the site and on GitHub.
- **Search reads every page.** The search dialog (press `/`) still finds skills, packs, loops and guides by name first, and now adds matches from the full text of every guide, skill, pack, loop and release below them, with the matching words highlighted.
- **Pages render more of their markdown.** Nested lists, numbered lists that start past 1, checklists, quoted example documents with their own headings and lists, `_emphasis_`, strikethrough and bare links now show as written. On skill pages, nested steps had been flattened into one line, and example inputs into one paragraph.
- **Link previews show plain text.** A skill shared in a chat no longer shows `**bold**` marks in its description.

## 0.16.11 — 2026-10-16

- **`skilldrop update` now updates installed loops.** `outdated` lists a loop whose version moved, `update` brings it current and keeps any file you edited beside the new one as `<file>.upstream`, and `diff` and `doctor` work on loops too. The four loops renumbered in 0.16.10 (`release`, `operate`, `ship-a-draft`, `apply`) are now version 0.3.0, so `npx skilldrop-cli update` takes them. Every loop now has to declare a `version`, and it moves whenever the loop changes.
- **Every how-to fits on a page.** Eight long how-tos were split: the task stays on the how-to, under 400 words, and the flags, paths and edge cases move to new reference pages for install options, install targets, updates and the ledger, the GitHub Action, benchmark options, the loop and skill contracts, and MCP servers. The check fails a how-to over 400 words.
- **New how-to: [Release a change](guides/how-to/release-a-change.md)**, the `release` loop from rollout plan to go/no-go, filed under the release stage in the docs.
- **[Skills that ship scripts](guides/reference/skills-with-scripts.md) lists every one of them**, with the packages, environment variables, hosts, programs and files each declares, generated from the manifests.

## 0.16.10 — 2026-10-16

- **An operating model page shows the whole method on one page.** The [operating model](guides/explanation/operating-model.md) puts the five stages, the gate that ends each one, the pack that helps there, and the packs for any stage in one picture, then says where the agent waits for you and what every verdict means. The picture is generated from the loops themselves, so it changes when a loop does.
- **Gate codes now follow the order of the work.** The whole number is the loop's place in the lifecycle and a decimal is a second gate inside it: `release` stops at G3 and G3.1 (were G2.5 and G2.6), `operate` at G4 (was G3), `ship-a-draft` at G5 (was G4), and `apply` at G6 and G6.1 (were G5 and G6). `discover`, `design` and `build` keep G0, G1, G2 and G2.1. To get the renumbered loops, install them again: `npx skilldrop-cli install --loop release operate ship-a-draft apply` (`update` refreshes skills, not loops). A loop run log written before this release still holds the old codes.
- **The docs are arranged by stage.** The sidebar opens with Start here, then one group per stage with that stage's loop, tutorial and pack guides, then everything else by kind. A page that belongs to a stage shows it above its title.
- **The guides follow one page standard**, checked on every commit: a how-to opens with what you can do, headings name the task instead of a step number, and filler words fail the check. The tutorial "From idea to shipped feature" now includes the `release` loop, and several pages had counts that no longer matched the catalogue corrected.

## 0.16.9 — 2026-10-05

- **`job-fit-analysis` gives a verdict that matches its own table.** It names the requirements you don't meet in its first line instead of counting them, credits a general ability such as dealing with the public from any job that plainly involves it, and no longer suggests rewording a partly met requirement so it reads as met. Two blind judges now prefer it in 13 and 11 of 15 pairs, up from 8 and 5 of 10.
- **24 more evals for 12 older skills**, written from each skill's description alone, so their numbers rest on five evals each and not three.
- **A second revision of those 12 skills was measured and not released.** Tested before and after on evals it had never seen, it moved the blind preference from 21 and 15 of 48 pairs to 24 and 17, which is no real change, and made each run cost more. [What the benchmark showed](guides/explanation/what-the-benchmark-showed.md) has the account. The published numbers now cover 209 evals: skills preferred in 61% of pairs by both judges.

## 0.16.8 — 2026-10-05

- **New skill: `application-form-answers`** (`career`). Give it a job application form and your resume. It drafts the answers your resume settles and the short written ones inside their word limits, fills in the form file when you ask it to, names the honest answers that could screen you out, and hands back the declarations that are yours alone (right to work, salary, start date, conflicts, monitoring questions) with what on your resume bears on each.
- **`resume-tailor` works in your resume's own format.** A resume kept as Typst, LaTeX or Word source is edited as a copy of that source and built when the tool is there, not handed back as Markdown. It treats the page count as a budget, lists every line it cut and every fact it added from outside the resume, and uses other material you point it to, such as a LinkedIn summary.
- **`job-fit-analysis` looks beyond the resume.** Evidence in another file of yours counts and is marked as not yet on the resume, and it asks once whether a side project, portfolio or volunteer role covers a gap. Given a posting link it cannot open, it says so and gives no verdict.
- **The `apply` loop gained a `form` stage**, and its last step now shows you four lists before you send anything: what is not claimed, what was added from outside the resume, what was cut, and the form questions only you can answer.
- **`claim_check.py` reads resumes kept as Typst or LaTeX source** and no longer lists names containing an ampersand as new.
- **These changes came from an end-to-end trial of the pack on realistic input** (RFC-0043): a resume kept as Typst source, a posting given as a link, and an online form. The new skill lost on its first held-out evals and was revised once; on two fresh ones it won 4 and 3 of 4 pairs with the two judges. Across the pack, the skills won 14 and 14 of 16 pairs on evals they were never revised against. The published numbers now cover 185 evals: skills preferred in 62% and 64% of pairs.

## 0.16.7 — 2026-10-05

- **New pack: `career`, for anyone applying for a job in any field.** `job-fit-analysis` compares a posting with your resume and says whether to apply, with what could get the application rejected listed first. `resume-tailor` reworks your resume for the posting and keeps every employer, title, date and number as you had them. `cover-letter` writes a letter under a page that says nothing about you or the employer that you or the posting didn't supply. Install it with `npx skilldrop-cli install --pack career`.
- **New loop: `apply`.** Fit check, tailored resume, cover letter, then a clean-up pass. You decide whether to apply before anything is written, and you confirm every line is true before anything is sent. The loop never submits an application.
- **A script that lists what a draft says that your resume doesn't.** `claim_check.py` ships with `resume-tailor` and `cover-letter`: give it a draft, your resume and the posting, and it prints every figure and named thing the draft contains that your own material does not.
- **The pack was admitted on a measured result** (RFC-0042). On 14 resume and letter requests, plain Claude Code added something the person never said in 11 of 28 documents, and the skills in 1. Two blind judges preferred the skills' result in 10 and 11 of 12 pairs on evals the skills had never seen. See [Does the agent invent your resume?](guides/explanation/resume-fabrication-comparison.md).
- **Twelve older skills were tested on evals they had never seen, and lost.** Both judges preferred plain Claude Code in about 7 pairs of 10. [What the benchmark showed](guides/explanation/what-the-benchmark-showed.md) gives the full account, and the published numbers now cover all 174 evals: skills preferred in 60% and 61% of pairs.

## 0.16.6 — 2026-10-02

- **31 skills answer first and stick to what you gave them.** Each now opens with the answer or the artifact, leaves out facts, names and numbers you didn't supply and lists what's missing once under "To confirm", works from what it has instead of stopping to ask, and keeps its own vocabulary out of the reply. Each also carries one rule of its own; for example, `release-notes` writes one set of notes and doesn't invent a product name, and `tech-comparison-matrix` leads with the recommendation.
- **`strategy-analysis` runs the framework you asked for in full**, then says in a few sentences which one fits the question better and offers to run it.
- **The benchmark now shows a preference for skills.** Across all 131 evals, two blind judges preferred the skill's result to plain Claude Code's in 61% and 63% of pairs, with both ranges above even, up from 56% and 57%. The 31 revised skills went from 17% and 20% to 35% and 37%; part of that is fitted to the evals they were revised against, and they meet slightly fewer of their own checks (60%, from 65%). Numbers and method are on the [How skills are checked](https://sananthanarayan.github.io/skilldrop/evals/) page.

## 0.16.5 — 2026-10-02

- **New guide: [Benchmark skills against the agent without them](guides/how-to/benchmark-skills.md).** How to run `run_bench.py` on this catalogue or your own, what each number means, and how to improve a skill against it.
- **The site's home page shows the benchmark result**, and the `grc` and `dev-team` pack pages cover the three skills added in 0.16.4.

## 0.16.4 — 2026-10-02

- **New skill: `pr-description-writer`** (`dev-team`). Writes a pull request title and description from the diff: why, what changed, the checks that were really run, where a reviewer should look first, and risk and rollback. It also reports what the diff contains that the commits don't mention, such as a dependency bump, a deleted test or a migration.
- **New skill: `tech-debt-register`** (`dev-team`). Turns notes, TODOs and incident write-ups into a ranked register: where each item lives, what it costs today with the evidence, the fix size, a decision and the trigger that reopens it. A cost nobody measured is marked as reported, never estimated.
- **New skill: `security-questionnaire-response`** (`grc`). Drafts answers to a customer's security questionnaire from your own policies and reports, in the customer's form, with the document behind each answer. Questions the evidence doesn't cover are marked as needing input, and conflicts and stale evidence are flagged for the security owner.
- **These three were admitted on a benchmark result** (RFC-0041): three evals each, two trials, two blind judges. Both judges preferred their results to plain Claude Code in 15 and 16 of 18 pairs after one revision. The RFC records the first round too, where they did not clearly win.

## 0.16.3 — 2026-10-02

- **The package, the plugin and the site now say what sets skilldrop apart:** portable skills, measured against the agent without them. The numbers behind that are on the [How skills are checked](https://sananthanarayan.github.io/skilldrop/evals/) page.
- **`run_bench.py --second-judge MODEL`** runs the blind comparison with a second model and reports how often the two judges agree. The published run now includes it.

## 0.16.2 — 2026-10-02

- **29 skills stop showing their machinery.** Replies and artifacts no longer mention the skill, its files, caps or internal terms, or that a run is non-interactive, and they name another skill once, at the end, as a next step. This came from the first benchmark run, where a blind judge marked those replies down.
- **A `BLOCKED` reply now tells you something.** In 13 skills the `BLOCKED: need <X>` line is followed by what is missing in plain words, what you'll get once it's supplied, and anything the request already allows.
- **`adr-generator` records a decision you've already made as `Accepted`.** "We decided" used to produce `Proposed`. Deciders, dates and drivers you didn't give are left out or marked, not guessed.
- **`delivery-metrics-report` no longer stops an unattended run on timestamps with no time zone.** It assumes UTC, says so at the top with the number of rows affected, and says what moves if that's wrong.
- **`strategy-analysis` gives you the framework you asked for.** When another one fits the question better it still says so and runs that one, and now adds yours after it.
- **`agents-md-generator` writes a missing command as a plain "none defined" line** in the file. The `[missing]` marker stays in the provenance table only.
- **Every skill is now measured against plain Claude Code**, with the results on the [How skills are checked](https://sananthanarayan.github.io/skilldrop/evals/) page. 22 evals gained the input files their prompts name, under `evals/files/`.

## 0.16.1 — 2026-10-01

- **`md-to-xlsx` no longer writes a workbook Excel can't open** when a cell holds a number too big to store, such as `1e999`. It is kept as text. A JSON integer longer than 15 digits is kept as text too, so an ID isn't rounded.
- **`md-to-xlsx` tells you when it removes an HTML tag from a table cell.** A name like `Fabrikam <Ltd>` used to lose `<Ltd>` without a word.
- **`file-to-markdown` keeps code blocks and quotes from a Word file.** Code comes back fenced with its indentation, quotes come back with `>`, and literal `<tag>` text is escaped so it survives being converted again.
- **`md-to-docx` says each warning once.** A 60,000-row table with the same problem in every row printed 60,000 lines.
- **`pre-merge-review --install-hook` respects your umask.** The pre-commit hook was always made world-readable (CodeQL `py/overly-permissive-file`); it now gets the execute bit only where the file was already readable.
- The three converter scripts run without deprecation warnings on Python 3.14.

## 0.16.0 — 2026-10-01

- **Pin a third-party catalogue to an exact commit:** `--from <url>#<commit-sha>`. A tag or branch can be moved to different code after you reviewed it, but a commit can't, and the CLI checks it got the commit you asked for. Every install records its commit in the ledger. An unpinned install prints the `#<commit>` URL that gets exactly those files again. Pinned skills stay put on `update` until you re-pin.
- **`outdated` and `update` catch a skill that changed upstream under the same version**, which the version check alone missed. `update` names it and leaves it alone; read it with `skilldrop diff`, then take it with `update --changed`.
- **Skills that ship scripts now declare what those scripts do** (`permissions` in `manifest.json`): the hosts they contact, the programs they run, and where they write. `skilldrop scan` raises any script that does something its skill doesn't declare as a top-severity finding, and `skilldrop validate` fails the catalogue. `skilldrop info` and third-party installs show the declaration. All 24 bundled script skills declare theirs.
- **The scan's network rule catches more:** every `requests` call form, `urlopen`, `http.client` and `aiohttp`. It had missed `figma-diagrams`'s calls to the Figma API.
- **New guide: [Use skills with MCP servers](guides/how-to/use-with-mcp-servers.md).** Which servers (GitHub, Atlassian, Linear, Figma, Sentry, Supabase, AWS cost, Slack) pair with which skills, how to add one in Claude Code, Cursor, Codex, VS Code, Kiro and Antigravity, and how to do it safely. Every endpoint and config key was checked against the vendor's docs.
- The OWASP mapping is updated: update drift (AST07) is now covered, and supply chain (AST02), over-privileged skills (AST03) and cross-platform reuse (AST10) are stronger. Ideas not yet built are collected in [docs/designs/future-ideas.md](docs/designs/future-ideas.md).
- The Claude plugin marketplace now has a description, so `claude plugin validate` passes without a warning.

## 0.15.1 — 2026-10-01

- `file-to-markdown` gets far more out of a PDF. Tables with aligned columns come through as Markdown tables, indented lists stay lists, code stays code, and short standalone lines become headings (it says those were guessed). A table whose cells wrap is kept as aligned text. A page with two columns of prose side by side is read in column order, and the script names those pages. Before, every PDF came out as run-together paragraphs.
- `mermaid-render` shows Mermaid's own parse error ("Parse error on line 6 …") when mermaid-cli can't draw a diagram, not a browser stack trace. Its lint agreed with real Mermaid (mermaid-cli 12.0.0) on all 57 diagrams tested: every one in the repo plus 21 edge cases.
- The `terraform-module` example now passes `terraform fmt -check` and `terraform validate` (Terraform 1.16.4), with the AWS provider at 5.0.0, 5.100.0 and 6.67.0. That's both ends of the range it declares. `terraform-plan-review`'s script was checked against real plans from Terraform 1.16.4, and flags an IAM wildcard, a public bucket policy and open SSH, without ever printing a secret from the plan.

## 0.15.0 — 2026-10-01

- Every pack has a how-to and a reference page in the docs: install it, run its first task, follow a typical session and its loops; then every skill's output, needs, quality bar, hand-offs and what it isn't for. They're generated from the skills' own files, so they stay current. Find them under *Per pack* in the docs.
- `skilldrop package <dir> --pack dev-team,design` copies a vetted subset of the catalogue into a standalone one you can host on an internal git server. `MIRROR.json` records where every file came from and its SHA-256.
- `skilldrop init-catalogue <dir>` starts a private catalogue for your team's own skills, with an example skill and a workflow that validates and scans every pull request.
- Loops can keep a local log of their gate verdicts. Set `SKILLDROP_LOOP_LOG` to a file path, and `skilldrop loop-stats` shows which gates pass first time, which loop back, and which block. Nothing is sent anywhere. See [Measure your loops](guides/how-to/measure-your-loops.md).
- skilldrop is now dual-licensed: MIT or Apache-2.0, at your option.
## 0.14.0 — 2026-10-01

Eight new packs and 28 new skills (93 in all, across 17 packs). Install any pack with `npx skilldrop-cli install --pack <name>`; each brings `core`.

- **converters**: `md-to-docx`, `md-to-xlsx` and `md-to-html` turn Markdown into Word, Excel and a self-contained HTML file, in your brand.json's fonts and colours. Excel cells are typed, so numbers, percentages and dates sort and sum. `file-to-markdown` turns .docx, .pptx, .xlsx, HTML, CSV and JSON back into Markdown, and lists what it dropped. `mermaid-render` finds the errors that stop a Mermaid diagram rendering, with the line, then renders it. All of them are standard-library scripts, with nothing to install.
- **experience-design**: `information-architecture`, `ux-writing`, `content-design` (with a readability check on the before and after), `design-system-spec` and `service-blueprint`.
- **research**: `research-plan`, `source-synthesis` (a script checks that every claim cites a listed source) and `hypothesis-comparison` (competing explanations ranked by how little evidence contradicts them).
- **trackers**: `backlog-triage` finds duplicates, missing owners and acceptance criteria, and stale items in a Jira, Linear or GitHub export. `team-status-report` builds a weekly status whose numbers come from the export, with the rule that set its RAG. `tracker-brief-sync` turns a PRD into importable issues and reports drift between the two.
- **data-analytics**: `metric-definition`, `sql-review` (correctness first: fan-out joins, NULLs, time zones, with corrected SQL) and `dashboard-spec`.
- **grc**: `dpia`, `soc2-evidence-map` and `risk-register`, which checks a register CSV and prints a heat map. They prepare material for a qualified reviewer; they aren't legal or audit advice.
- **infra-as-code**: `terraform-module` writes a module with secure defaults. `terraform-plan-review` reads `terraform show -json` and gives SAFE TO APPLY, APPLY WITH CARE or DO NOT APPLY, naming every destroy, replacement and widened permission.
- **skill-engineering**: `skill-author` writes a portable skill with evals for any tool. `skill-review` audits one, with a lint script, and ends READY, FIX FIRST or REWRITE.
- **sre-oncall** adds `delivery-metrics-report` (DORA's four metrics and flow metrics, computed from your deploy and incident exports) and `cloud-cost-review` (waste and savings in an AWS, GCP or Azure cost export, with savings computed from the bill's own rates). `capacity-cost-model` now covers forward-looking estimates only.
- Five new jobs to browse by on the site: design the experience, research a question, define and trust the numbers, manage risk and compliance, and build agent skills.

## 0.13.9 — 2026-10-01

- The `claude-api` pack is now **`api-builder`**, because Claude Code now rejects plugin names that start with `claude-`, which could stop the whole marketplace from loading. Install it with `npx skilldrop-cli install --pack api-builder` or `/plugin install api-builder@skilldrop`. The old `--pack claude-api` still works, with a note, and the old pack page redirects. If you installed the `claude-api` plugin, uninstall it and install `api-builder`. The four skills are unchanged.

## 0.13.8 — 2026-10-01

- New install targets: `--ide codex`, `--ide antigravity` and `--ide copilot`. Each installs to the tool's personal skills folder, or into the repo with `--project` (`.agents/skills` for Codex and Antigravity, `.github/skills` for Copilot). `--panel review` works with all three.
- `--local` lets you try skills in a repo you don't own. It installs into the repo and lists every file in `.git/info/exclude`, so `git status` stays clean and nothing can be committed by accident. `uninstall --local` removes both the files and the entries.
- `--dry-run` on `install`, `update`, `uninstall` and `new-skill` shows exactly what would change, including which of your edited files would be overwritten, and changes nothing.
- `uninstall` and `update --force` ask before going ahead when you're at a terminal, and name any files you edited. `--yes` skips the question; scripts and CI are never asked.
- `skilldrop diff <skill>` shows how your installed copy differs from the catalogue's, file by file: your edit, a catalogue change, or both.
- `skilldrop doctor` checks an install against its ledger and reports missing skills, `.upstream` files waiting to be merged, and leftover wiring or hooks, each with the command that fixes it. It changes nothing.
- `skilldrop new-skill <name> --pack <pack>` scaffolds a skill with `SKILL.md`, `manifest.json` and both eval files, and registers it in `model-routing.json`. `skilldrop --version` prints the version.
- `skilldrop scan` tags each finding with its OWASP Agentic Skills Top 10 and LLM Top 10 2025 IDs. It now scans every markdown file in a skill, not only `SKILL.md`, and flags a skill that tells the agent to fetch instructions from a URL at run time. `update` scans skills from third-party catalogues again after updating them. [skilldrop and the OWASP Top 10s](guides/reference/owasp-mapping.md) maps each control and names the gaps.
- `agent-threat-model` tags every 🟥 and 🟧 path with its OWASP IDs, from a mapping table in its reference.
- Every skill now ships acceptance evals and trigger queries. The 14 that had none got them, and `validate.py` now requires both files. A new page on the site, *How skills are checked*, lists each skill's evals, and each skill page shows its assertions and trigger queries.
- A weekly workflow runs the trigger queries against a live model and reports which ones go to the wrong skill. It's report-only and needs an `ANTHROPIC_API_KEY` secret. `python3 run_evals.py` runs the same check locally, and `--assertions` grades the acceptance evals too.
- The repo is now a GitHub Action: `uses: sananthanarayan/skilldrop@<sha>` with `skill: doc-critique` runs a skill on a pull request's diff, writes the result to the job summary, and can fail the check on a verdict. See [Run a skill in CI](guides/how-to/run-a-skill-in-ci.md).
- Each pack page has *A typical session*: what you bring, then each step's skill with what you type, what you get and where you decide.
- Every release has its own page at `changelog/<version>/`, and `changelog/feed.xml` is an Atom feed for feed readers and Slack.
- Issue templates for bugs and skill requests, and a pull request template with the pre-commit checklist.
- CI scans every push for secrets (gitleaks), workflow errors (actionlint) and workflow security problems (zizmor).

## 0.13.7 — 2026-10-01

- `install --with-hooks` and `uninstall` work inside a git worktree or submodule, where `.git` is a file rather than a folder. Both crashed there before. The pre-commit reminder now goes wherever git reads hooks from, including a custom `core.hooksPath`.

## 0.13.6 — 2026-10-01

- New **design** pack: `npx skilldrop-cli install --pack design` gets on-brand decks and flyers, with `core`.
- `brand-kit` captures your brand once as a `brand.json`: logo files (and an on-dark version), colours as hex codes, heading and body fonts, voice, imagery, your PowerPoint template, contact details and footer. Every value says where it came from, and a checker tests text contrast and catches missing or SVG-only logos.
- `marketing-flyer` makes a print-ready flyer in your brand, for an event, launch, offer or hiring drive. It's one HTML file that saves to PDF (or exports with `--pdf`, and `--png` for square and story social sizes), in four layouts, with one call to action and only the facts you gave it.
- `deck-builder` asks for your branding before it builds, and takes `--brand brand.json`. Without a template, it now puts your logo on every slide (the white version on dark slides) and uses your heading and body fonts. It and `slide-outliner` moved to the design pack; install them by name or with `--pack design`.

## 0.13.5 — 2026-10-01

- Every skill has its own page on the site, at `skills/<name>/`. Each page has one install command, a realistic prompt to try, what a good result looks like, what it hands off to, and its source. Catalogue rows link to it.
- Pack pages lead with one install command and fold the alternatives under "Other ways to install". A summary box above it says when to use the pack, which jobs it covers, where a person decides (each human or review gate), and how big it is.
- The packs index groups packs by the job in front of you, so you can start from "decide what to build" rather than a role name.
- Every page on the site (home, packs, skills, catalogue, docs, changelog) has the same navigation, and a new "What's new" page renders every release.
- The README is a short router: one line per role pack, one install command and its starter prompt, then links. The full skill list, the loop reference with its diagrams, and every install route now live in the docs portal, which renders tables and diagrams.
- `contribution-wizard` now tells authors to add a new skill's row to the skill catalogue guide rather than the README.

## 0.13.4 — 2026-10-01

- `npx skilldrop-cli install --profile <name>` works. The npm package was missing `profiles.json`, so profiles only worked from a clone of the repo.

## 0.13.3 — 2026-10-01

- Every pack now has a page with what to try first: a starter prompt to paste, how to tell it worked, and what to do if nothing happens. Browse them at `sananthanarayan.github.io/skilldrop/packs/`. The CLI prints the same starter after `install --pack`, or any time with `skilldrop info --pack <name>`, and each Claude pack plugin carries it in a README.
- Skills now live in their pack's folder: `packs/<pack>/skills/<name>/`, with loops at `packs/<pack>/loops/<name>/` and each pack's metadata in `packs/<pack>/pack.json`. To copy a skill by hand, use `cp -R packs/<pack>/skills/<name> ~/.claude/skills/`. Installs through the CLI, `pack.py` or the Claude plugins work as before, and `outdated` and `update` carry on across the move. An older CLI pointed at this repo with `--from` needs upgrading; flat `skills/` catalogs from other people keep working.
- `skilldrop install --profile <name>` works. It had been reading the profile name as missing.

## 0.13.2 — 2026-10-01

- `skilldrop update` no longer erases your edits to an installed skill. A file you changed is kept, and the new version is written next to it as `<file>.upstream` for you to merge. Files you didn't touch update as before, and `--force` still overwrites everything. Skills installed with an earlier version overwrite once on their next update, then keep edits from then on.
- Packs are re-cut so every skill and loop has exactly one home. A new `core` pack holds the skills every role uses (`brief-intake`, `doc-critique`, `output-hygiene`, `council-review`) and the `ship-a-draft` wrapper. Every role pack except `claude-api` installs `core` with it, through the CLI, `pack.py` and the Claude plugins alike, so one `--pack` command still gives a role its whole toolkit.
- Eight skills moved to a single pack: `user-story-splitter`, `launch-readiness` and `agents-md-generator` → `dev-team`; `capacity-cost-model` → `sre-oncall`; `data-contract` → `solution-architect`; `agent-threat-model` and `ai-use-case-triage` → `ai-engineering`; `exec-summary` → `stakeholder-comms`. If you installed a pack for one of these, install it by name or add the pack that now holds it.
- The `full` profile now includes every pack and every loop. It had been missing `claude-api` and `release`.

## 0.13.1 — 2026-10-01

- Run the new `release` loop to take merged code to live users: `migration-plan` plans the rollout and the rollback, `launch-readiness` judges readiness at G2.5, `release-notes` drafts the announcement, and a human makes the go/no-go call at G2.6. Install it with `skilldrop install --loop release`, or get it in the `dev-team` and `sre-oncall` packs.
- Ask "are we ready to launch?" and `launch-readiness` returns a go/no-go report: the change's own failure modes, then seven checks, each with evidence and an owner role. A missing rollback blocks the launch on its own, and detection or runbook gaps are handed to `observability-plan` and `runbook-generator`.

## 0.13.0 — 2026-09-30

- Browse every guide in a full docs portal at `sananthanarayan.github.io/skilldrop/docs/` — each of the 22 guides renders as a standalone HTML page with a persistent sidebar grouped by Diátaxis kind (tutorial, how-to, reference, explanation) and a live client-side search box that filters by title, summary, and body text.
- Install `skilldrop install --pack claude-api` to get four new skills for teams building on the Anthropic API: `prompt-caching-advisor` identifies where to insert `cache_control` checkpoints and estimates the cache hit rate; `token-budget-estimator` breaks down input/output token usage by workflow component and names the dominant cost driver; `eval-harness-generator` reads a SKILL.md and produces 8–12 eval cases covering happy path and edge cases; `tool-use-schema-writer` converts a plain-language function description into a valid Anthropic tool definition with a Python usage snippet.
- `contribution-wizard` guides an author through creating a new skill from scratch — one intake block generates the manifest, SKILL.md, eval cases, and README entry.
- Five new how-to guides cover integrating skilldrop with Jira, GitHub Projects, Figma, and Linear (which skills to use, what to paste, what to expect back), plus a credential brokering guide for skills that declare `env.required` — local shell, GitHub Actions secrets, and enterprise vault patterns.
- Two end-to-end scenario walkthroughs show the loops in action: "From complaint to closed incident" traces a Monday-morning support spike through the discover and operate loops with gate verdicts at each stage; "From idea to shipped feature" moves a product idea through all four lifecycle loops with a real refusal at every gate (G0 REVISE, G1 PROCEED WITH CONDITIONS, G2 BLOCKED, G3 postmortem delta).
- The catalogue site now has hero entrance animations, scroll-triggered reveals, animated stat counters that count up from zero on scroll, card hover lift, CTA glow, a nav logo shimmer, and a scroll-activated backdrop blur — all CSS and vanilla JS with no new dependencies.

## 0.12.2 — 2026-09-30

- `skilldrop bootstrap` writes the skilldrop marketplace into `~/.claude/settings.json` so
  every Claude Code session on the machine discovers the catalogue without any per-session
  `/plugin` command — one command for onboarding scripts or provisioning runbooks.
- The catalogue site now serves `marketplace.json` at a stable URL
  (`sananthanarayan.github.io/skilldrop/marketplace.json`) so org admins can point internal
  tooling at it directly.
- `pages` CI now guards `marketplace.json` against drift before deploying the site, so a
  stale marketplace is caught on PRs rather than after the merge.

## 0.12.1 — 2026-09-28

- `deck-builder` builds on your own PowerPoint template: point `template` at a `.potx`/`.pptx`
  and the deck inherits its masters, theme fonts, colours, logos and slide size. Discover the
  template's layouts with `build_deck.py --list-layouts brand.potx`, then bind each logical
  layout to one in `layout_map`. Placeholders are filled without flattening the brand's
  typography, and unfilled ones are deleted so no "Click to add text" ghosts survive.
- `deck-builder` gained three evidence layouts — `chart` (column, bar, line, stacked, pie,
  doughnut, with a required takeaway and source), `table` (styled header, zebra rows,
  auto-shrinking type), and `image` (aspect-fit, full-bleed or paired with bullets). A missing
  or non-raster image draws a labelled placeholder and warns instead of failing the build;
  `--strict` turns that into a hard error for CI.
- `deck-builder` asks for audience, format, time budget and design in **one** setup block with
  defaults pre-chosen, instead of asking about the palette alone — and honours `"aspect": "4:3"`
  for decks that aren't 16:9. Slide numbers appear automatically past 10 slides.

## 0.12.0 — 2026-09-25

The milestone the 0.11.6–0.11.9 releases were building toward.

- **skilldrop is an operating model now, not a catalogue.** Install one command and get a way of working — five loops over 57 skills, six named gates, one verdict vocabulary — instead of 57 things to choose between. A loop *orders* skills and never contains one, so all 57 still install and run alone by folder copy, and the whole thing still has zero runtime dependencies.
- **Five loops.** `discover` → `design` → `build` → `operate` cover the lifecycle and are separated by **reversibility** — a re-brief, months unwound in code, a revert, live users — which is also what decides whether a script, a review panel, or a person holds the gate. `ship-a-draft` wraps any generator. Install one with its stage skills: `skilldrop install --loop build`.
- **Gates that can actually refuse.** Six named gates (G0–G4) answering from one shared vocabulary in five classes, so `READY`, `PROCEED` and `SHIP IT` are recognisably the same kind of answer — and `validate.py` rejects a gate that can only succeed, one that cannot say `BLOCKED`, or one that invents a new word for an existing outcome.
- **Directed hand-offs with a mandatory `fallback`**, which turns "sibling hand-offs are advisory" from prose an agent may ignore into something the linter checks. 22 edges across 15 skills.
- **A closed contract per primitive** in `contracts/` — skills, packs, loops, agents, guides — checked by a ~50-line stdlib JSON Schema subset. `"tier": "claude-opus-5"` now fails the lint instead of only the style guide.
- **Docs a stranger can actually use:** `ARCHITECTURE.md`, a Diátaxis `guides/` tree with a full walkthrough tutorial, and a README down from 714 to ~525 lines.
- **`llms.txt`** so a model reads the handful of pages that matter instead of crawling 400+ files. Generated and drift-checked, because a stale index a model trusts is worse than no index.

New in this release specifically:

- New [`llms.txt`](llms.txt), generated from `packs.json`, the loop contracts, `contracts/` and guide frontmatter. Served from the repo root and the site root.
- The site leads with the operating model: new hero, **Loops** second in the nav and second on the page, **Outcomes** promoted from filter chips to a section, and a **Docs** section surfacing `ARCHITECTURE.md`, the guides and `llms.txt` — all previously near-invisible to a visitor.
- New tutorial: [Follow one change through the loops](guides/tutorial/follow-a-change-through-the-loops.md) — one realistic change from a stakeholder complaint to a closed incident, organised around what each gate refuses.
- All five loops ship acceptance evals — 10 cases, 35 trigger queries, shape enforced. Two encode failure modes a stage table cannot prevent: routing a revise to the wrong stage, and treating `PROCEED WITH CONDITIONS` as `PROCEED`.

## 0.11.9 — 2026-09-25

- Every primitive now has a **closed, machine-readable contract** in `contracts/` — skills, packs, loops, agents, and guides. `validate.py` checks each instance against its schema, so a typo'd manifest key fails instead of being ignored, and `"tier": "claude-opus-5"` is finally rejected by the lint rather than only by the style guide. Checked by a ~50-line stdlib JSON Schema subset: skilldrop still has zero runtime dependencies.
- New **`ARCHITECTURE.md`** — the four primitives, why a loop is not just a long skill, why the loops are separated by reversibility, the copy-never-transform install contract and its one exception, and the five invariants worth protecting.
- The README is 714 → 522 lines. Per-IDE install steps, hooks, catalogue publishing, script-shipping skills, and the authoring paths moved into **`guides/`**, split by Diátaxis kind declared in frontmatter rather than by directory. A guide that is not linked from `guides/README.md` fails the lint, because an unindexed guide is unfindable.
- New guides for authoring: [Author a new loop](guides/how-to/author-a-loop.md) and [Why loops](guides/explanation/loops.md), which explains why sequencing is its own primitive and why there are four lifecycle loops rather than three.
- Fixed a blank line that made the reviewer-agents table render as two broken tables on GitHub.

## 0.11.8 — 2026-09-25

- Loops are installable: `skilldrop install --loop build` puts the loop *and* every stage skill it sequences into your tool in one command. `--no-skills` installs the loop alone — it still runs, because each stage degrades through its declared `fallback`. `--loop --pack sre-oncall` installs every loop a pack declares.
- `skilldrop loops` lists the five loops with their stages and gates; `--json` emits the whole shape for tooling. `skilldrop uninstall --loop <name>` removes a loop and leaves its stage skills in place.
- A loop installs as an ordinary invokable skill. `LOOP.md`'s frontmatter is already `SKILL.md`'s shape, so it projects to `<dest>/<name>/SKILL.md` with `loop.json` beside it — no target needs a loop primitive of its own.
- Role packs now declare their loops, so `dev-team` brings `build`, `sre-oncall` brings `operate`, and `product-manager` brings `discover`. `validate.py` checks both directions, and refuses a loop whose name collides with a skill's.
- The catalogue site gained a **Loops** section, a loops stat tile, and a `loops` key in `catalogue.json`.
- Per-pack Claude Code plugins now carry their pack's loops, so `/plugin install sre-oncall@skilldrop` brings the `operate` loop with the runbook and incident skills it sequences.

## 0.11.7 — 2026-09-25

- Three more loops complete the lifecycle: `discover` (raw signal to a requirement a human ratifies at **G0**), `design` (a requirement to a recorded ADR, gated by `council-review` at **G1**), and `operate` (a shipped service through detection, response and learning at **G3**). With `build` and the `ship-a-draft` wrapper, skilldrop now ships five loops.
- The four lifecycle loops are separated by **reversibility** — a discovery mistake costs a re-brief, a design mistake is unwound in code months later, a build mistake is a revert, an operate mistake reaches live users — which is why each owns its own gate instead of folding into a neighbour.
- `operate` closes a real feedback edge: `postmortem-generator` emits runbook deltas and the loop routes them straight back into `runbook-generator`.
- Skills can now declare a **directed** hand-off: `handoff: [{ to, when, purpose, fallback }]`. `fallback` is required, which turns "sibling hand-offs are advisory" from prose into something `validate.py` checks — a hand-off to a skill you have not installed now degrades in a stated way instead of dead-ending. 22 edges ship across 15 skills.
- Loop diagrams are generated from `loop.json` by the new `build_loops.py`, into `docs/loops/*.mmd` and the README's mermaid blocks. `validate.py` fails on drift, so a diagram can no longer disagree with the contract it illustrates. The two hand-maintained `.mmd` files this replaces are retired.

## 0.11.6 — 2026-09-25

- skilldrop now ships **loops**, not just parts. A loop is a named sequence of stages over existing skills with a gate between them — `loops/build/` takes an agreed requirement to merged code behind a mechanical gate, and `loops/ship-a-draft/` wraps any generator in structured intake before and critique plus a machine-residue scrub after (RFC-0028).
- A loop sequences skills but never contains one, so all 57 skills stay independently installable and a single-folder copy still works in Cursor, Kiro, and Aider.
- Every gate now answers from one shared verdict vocabulary (`contracts/terminals.json`) in five classes — pass, conditional, revise, redirect, blocked — instead of each skill inventing its own word for the same outcome.
- The two pipeline diagrams that lived only as README prose are now backed by machine-readable `loop.json` contracts that `validate.py` enforces: named skills must exist, gate ids are repo-unique, a mechanical gate's script must be real, and a gate that can only succeed is rejected.

## 0.11.5 — 2026-09-18

- Role packs are now installable as Claude Code plugins: `/plugin install solution-architect@skilldrop` after the same one-line `marketplace add`. A pack carries the reviewer subagents its own skills delegate to, so `dev-team` brings the review panel and `sre-oncall` does not (RFC-0027).
- Retired the generated `agentbundle-catalogue` branch and its exporter. It was never documented as an install path, and its publish was gated by a third-party verifier that had moved 24 minor versions since the export was written. Reading agentbundle-shaped catalogues with `skilldrop --from <repo>` is unaffected.
- The README skill-count guard no longer misfires on per-pack counts inside a code block.

## 0.11.4 — 2026-09-18

- New skill `output-hygiene`: finds what a machine left in agent-written text — invisible Unicode, non-breaking spaces, homoglyphs, harness-added provenance trailers, trailing chat closers — and separates what is safe to strip from what needs a decision (RFC-0025).
- The catalogue page now opens with its search box and filters visible instead of hiding all 57 skills behind a disclosure toggle (RFC-0026).
- Filter state lives in the URL, so a filtered view — one pack, one tier, one outcome — is a link you can send someone.
- New browse axis: seven **outcomes** answer "why am I here", alongside the six role packs that answer "who am I".
- The site shows its own version and its three most recent releases, so a visitor can tell the project is alive.

## 0.11.3 — 2026-08-10

- `validate.py` fails when a shipped skill has no README row, so the catalogue can no longer document less than it ships.
- Every RFC carries an accurate status, and the pre-commit checklist says which rules are machine-enforced and which are human judgment.

## 0.9.3 — 2026-08-07

- New skill `agent-adoption-stage`: places a team on an agent-adoption curve and names the next move (RFC-0024).

## 0.9.2 — 2026-08-07

- Four AI-adoption skills: `ai-readiness-assessment`, `ai-use-case-triage`, `ai-adoption-rollout`, `ai-usage-policy` (RFC-0023).

## 0.9.1 — 2026-08-06

- `skilldrop` read commands take `--json` (RFC-0021), so the catalogue is scriptable.
- Supply-chain scanning on the code that runs on other people's machines (RFC-0022).
- Evals backfilled across the activation-collision clusters that actually compete.

## 0.9.0 — 2026-08-05

- `skilldrop install --panel review` installs the whole reviewer panel in one command (RFC-0020).
- Model map refreshed to the Claude 5 family; conformance to the Agent Skills open standard declared.
