---
name: sonar-review
description: Run a Sonar scan against the just-changed code on the current branch and produce a structured compliance report — quality-gate verdict (PASS / FAIL), then severity-tagged findings (🟥 blocker / 🟧 critical / 🟨 major / ⚪ minor / ⚪ info) scoped to changed files, each with file:line, the Sonar rule ID, the category (bug / vulnerability / security hotspot / code smell), why it matters, and a concrete fix. Works against both **SonarQube server** (self-hosted) and **SonarCloud** (SaaS) — mode is detected from `sonar-project.properties`. Sister skill to `devils-advocate`, but enforces Sonar's rule catalog and the project's quality gate rather than a hand-rolled lens sweep. Use after writing code, before pushing or opening a PR, when the user says "is this Sonar-compliant?", "run Sonar on this", "will the quality gate pass?", or any pre-merge compliance check.
---

# sonar-review

You run a Sonar scan against the user's just-changed code and produce a structured pre-merge compliance report. The artifact is a markdown review the user acts on — not raw scanner output, not a quiet "scan complete".

This skill is the **Sonar-flavored counterpart to [`devils-advocate`](../devils-advocate/SKILL.md)**: same shape (severity-tagged findings, file:line evidence, concrete fixes, verdict on top), but the rules come from Sonar's catalog and the verdict comes from the project's quality gate, not your judgment.

Works against both deployment modes — the mode is detected from `sonar-project.properties`, not asked:

| Mode | Detection | Host | Token env |
|---|---|---|---|
| **SonarQube server** | No `sonar.organization` line | `$SONAR_HOST_URL` (set by user) | `$SONAR_TOKEN` |
| **SonarCloud** | `sonar.organization=<key>` present | `https://sonarcloud.io` (fixed) | `$SONAR_TOKEN` |

The API endpoints are identical between the two — only the host differs. If the user is jumping in cold and the repo isn't wired up, run [`sonar-onboard`](../sonar-onboard/SKILL.md) first.

## How to respond

1. **Detect the mode.** First thing — read `sonar-project.properties` and check for a `sonar.organization=` line:
   - **Present** ⇒ SonarCloud. Host is `https://sonarcloud.io` (don't read `$SONAR_HOST_URL`).
   - **Absent** ⇒ SonarQube server. Host comes from `$SONAR_HOST_URL`.

   Use the detected mode for every subsequent step. Don't ask the user — the properties file is the source of truth.

2. **Verify the environment before scanning.** Checks differ by mode:

   | Check | Applies to | If missing |
   |---|---|---|
   | `sonar-project.properties` at repo root | both | Stop. Tell the user to run `sonar-onboard` first — there's no project config to scan against. |
   | `sonar-scanner` on `PATH` | both | Stop. Print the install hint (see step 3). Do not attempt to install it. |
   | `SONAR_TOKEN` env var set | both | Stop. Tell the user to export it from their Sonar account → Security → Tokens. |
   | `SONAR_HOST_URL` env var set | **server only** | Stop. Tell the user to export it (e.g. `export SONAR_HOST_URL=https://sonar.company.com`). |

   These are non-negotiable. Don't fabricate findings, don't run a partial scan, don't fall back to a local linter — the artifact this skill produces is a *Sonar* report or it's nothing.

3. **Install hint** if `sonar-scanner` is missing — print verbatim, don't drive the install:

   ```
   sonar-scanner CLI not found on PATH. Install it:
     macOS:    brew install sonar-scanner
     Linux:    https://docs.sonarsource.com/sonarqube/latest/analyzing-source-code/scanners/sonarscanner/
     Docker:   docker run --rm -v "$(pwd):/usr/src" sonarsource/sonar-scanner-cli
   Then re-run this skill.
   ```

4. **Identify the change under review.** Same precedence as `devils-advocate`:
   - User has shown you a diff or named files — that's the scope.
   - Git working tree has unstaged + uncommitted changes — `git diff` is the scope.
   - User says "the feature I just built" — run `git diff origin/main...HEAD` (or `HEAD~1` if no upstream).

   The scope is the **set of changed files**, not the whole repo. The scan itself runs against the whole project (Sonar needs the full graph for accurate cross-file analysis), but **findings you report are filtered to changed files only** — anything else is out-of-scope noise.

5. **Set the host variable for the run.** Same logic, both modes:

   ```bash
   if grep -q '^sonar.organization=' sonar-project.properties; then
     SONAR_HOST="https://sonarcloud.io"  # SonarCloud is fixed
   else
     SONAR_HOST="$SONAR_HOST_URL"        # server reads env var
   fi
   ```

   Use `$SONAR_HOST` for both the scanner CLI and the API calls below.

6. **Run the scan.** From the repo root:

   ```bash
   sonar-scanner \
     -Dsonar.host.url="$SONAR_HOST" \
     -Dsonar.token="$SONAR_TOKEN" \
     -Dsonar.branch.name="$(git rev-parse --abbrev-ref HEAD)"
   ```

   Note on `sonar.branch.name`: SonarCloud accepts it on all tiers; SonarQube Community Edition does not. If you see `License not valid for branch analysis`, drop the flag and re-run — the scan will overwrite the default branch's history (acceptable for a local pre-merge check, not for CI).

   If the project uses Maven, Gradle, or `dotnet-sonarscanner`, prefer those wrappers (they hook into the compile step) — check `sonar-project.properties` and the build files to decide. See [`reference.md`](reference.md).

   The scan typically takes 30s–3min. **Wait for it.** Do not summarize before results land — a "should pass" guess is worse than waiting.

7. **Fetch the gate status and issues from the Sonar API.** After the scan finishes, the scanner writes `.scannerwork/report-task.txt` with a `ceTaskUrl` — poll it until `status=SUCCESS`, then fetch (same endpoints for server and cloud — only `$SONAR_HOST` differs):

   ```bash
   PROJECT_KEY=$(grep '^sonar.projectKey=' sonar-project.properties | cut -d= -f2)
   BRANCH=$(git rev-parse --abbrev-ref HEAD)

   # Quality gate
   curl -s -u "$SONAR_TOKEN:" \
     "$SONAR_HOST/api/qualitygates/project_status?projectKey=$PROJECT_KEY&branch=$BRANCH"

   # Issues (scoped to new code in this branch)
   curl -s -u "$SONAR_TOKEN:" \
     "$SONAR_HOST/api/issues/search?componentKeys=$PROJECT_KEY&branch=$BRANCH&inNewCodePeriod=true&ps=500"

   # Security hotspots
   curl -s -u "$SONAR_TOKEN:" \
     "$SONAR_HOST/api/hotspots/search?projectKey=$PROJECT_KEY&branch=$BRANCH&inNewCodePeriod=true"
   ```

   Filter the issues list to changed files (compare each issue's `component` field against the diff). See [`reference.md`](reference.md) for the exact JSON shapes.

8. **Map Sonar severities to the report's severity markers.** Keep the mapping consistent across reports:

   | Sonar severity | Marker | Meaning in the report |
   |---|---|---|
   | `BLOCKER` | 🟥 **Blocker** | Will ship a bug or security issue. Must fix before merge. |
   | `CRITICAL` | 🟧 **Critical** | High-impact bug, hotspot, or vulnerability that needs review before merge. |
   | `MAJOR` | 🟨 **Major** | Code smell or quality issue that will hurt within months. Fix before merge if reasonable. |
   | `MINOR` | ⚪ **Minor** | Quality nit. Fine to defer. |
   | `INFO` | ⚪ **Info** | Optional. List only if there are < 5 of them; otherwise summarize the count. |

   **Do not invent severity.** Sonar's catalog assigns it — copy it. The mapping is mechanical, not judgmental.

9. **Sweep the five lenses.** Sonar categorizes every finding into one of these — group the report by lens, same as `devils-advocate`. Each lens file describes what to look for and how to phrase the fix:

   | Lens | File | Sonar issue type |
   |---|---|---|
   | 1. Bugs | [`lenses/bugs.md`](lenses/bugs.md) | `BUG` |
   | 2. Vulnerabilities | [`lenses/vulnerabilities.md`](lenses/vulnerabilities.md) | `VULNERABILITY` |
   | 3. Security hotspots | [`lenses/security-hotspots.md`](lenses/security-hotspots.md) | `SECURITY_HOTSPOT` (separate API) |
   | 4. Code smells | [`lenses/code-smells.md`](lenses/code-smells.md) | `CODE_SMELL` |
   | 5. Coverage + duplication | [`lenses/coverage-and-duplication.md`](lenses/coverage-and-duplication.md) | Quality-gate condition failures |

10. **For every finding, write four parts** (same shape as `devils-advocate`):

   - **Where:** `file:line` — quote 5–15 chars of the offending line.
   - **Rule + category:** `[BUG · javascript:S2228] Console logging should not be used`. The rule ID is what the user clicks in the Sonar UI to read the catalog page.
   - **Why it matters:** one sentence — what the rule prevents *in this scenario*. ✅ "Mutable shared state in `parseConfig` will desync between requests under concurrent load." ❌ "Avoid shared state."
   - **Fix:** ✅ "Wrap the cache in `Object.freeze()` on line 23, or move the mutable copy inside `parseConfig` (preferred — matches the pattern in `parseUserConfig`:51)." ❌ "Refactor to avoid mutation."

11. **Open with the gate verdict, not the findings.** The first thing the user sees:

   ```
   Quality gate: ❌ FAIL — coverage on new code is 71% (gate requires ≥ 80%), 1 new vulnerability.
   Findings on changed code: 1 blocker · 3 critical · 7 major · 4 minor.

   The blocker is a SQL-injection-shaped query construction at api/users.ts:142 (rule javascriptsecurity:S3649) — parameterize before merging. The vulnerability and the coverage shortfall are what's failing the gate; the major findings are all in the new payment-handler module and are fixable with the patterns used elsewhere in the codebase.
   ```

   If the gate passed, lead with that and still report findings (a passing gate doesn't mean zero issues — it means the *new code* met the conditions; minor findings may still be worth fixing).

12. **Use [`templates/report.md`](templates/report.md)** for the output structure:

    ```markdown
    # Sonar review: {feature / PR title}
    _Scope: {N changed files} · Branch: {branch} · Scanned: {YYYY-MM-DD HH:MM}_
    _Sonar project: [{project-key}]({sonar-url}/dashboard?id={project-key}&branch={branch})_

    ## Quality gate
    {PASS / FAIL} — {one-line reason}
    {2-sentence summary, lead with what failed the gate}

    ## Findings on changed code
    {counts table}

    ### 1. Bugs
    ### 2. Vulnerabilities
    ### 3. Security hotspots
    ### 4. Code smells
    ### 5. Coverage + duplication

    ## Pre-existing issues touched (FYI)
    {issues in files you changed that pre-date this branch — for awareness, not blocking}

    ## Suggested order to address
    1. Fix anything failing the quality gate (blockers + vulnerabilities + coverage)
    2. Review the security hotspots — Sonar can't auto-decide, you have to mark them
    3. Major findings, especially anything in load-bearing or security-adjacent code
    4. Minors as time allows
    ```

13. **End with the Sonar dashboard link.** The full picture — including pre-existing debt, history, and the gate's detailed conditions — lives in the Sonar UI. Always end with `Full report: ${SONAR_HOST}/dashboard?id=<project-key>&branch=<branch>` — `$SONAR_HOST` is the value you set in step 5 (so the link works whether the project is on SonarQube server or SonarCloud).

## Useful references in this skill

- [`lenses/bugs.md`](lenses/bugs.md) — how to phrase Bug findings
- [`lenses/vulnerabilities.md`](lenses/vulnerabilities.md) — Vulnerability findings (CWE / OWASP-tagged)
- [`lenses/security-hotspots.md`](lenses/security-hotspots.md) — Hotspots need human review, not auto-fix
- [`lenses/code-smells.md`](lenses/code-smells.md) — Maintainability findings
- [`lenses/coverage-and-duplication.md`](lenses/coverage-and-duplication.md) — Gate conditions that aren't issues
- [`templates/report.md`](templates/report.md) — Report skeleton
- [`reference.md`](reference.md) — Sonar API shapes, Maven/Gradle/dotnet variants, scoping to PR diffs

## Quality bar

- **Verdict comes from the gate, not from you.** The quality gate is the source of truth. ✅ "Gate FAIL — 1 new vulnerability." ❌ "Looks risky to me." If the gate passed, say PASS even if you'd personally flag issues.
- **Findings are scoped to changed files.** The repo has pre-existing debt; this skill is a pre-merge check, not a backlog dump. Pre-existing issues in *touched* files go in a separate "FYI" section — issues in untouched files don't appear at all.
- **Every finding cites `file:line` and the Sonar rule ID.** `javascript:S2228` is a click-through to the Sonar UI catalog. Strip either and the finding becomes unactionable.
- **Severity is Sonar's, not yours.** Don't downgrade a `CRITICAL` because you disagree, and don't upgrade a `MINOR` to make the report scarier. If you disagree with the catalog, raise it in the lens body, don't rewrite the severity.
- **Fixes name a concrete change.** A patch line, a function rename, a missing test case — not "consider refactoring".
- **Don't recommend disabling rules to pass the gate.** That's a code-quality conversation. Suggest fixes or scoping (Sonar-scoping comments like `// NOSONAR` should be rare and justified in the code, not as a default).
- **Security hotspots are flagged for review, not "fixed".** Hotspots ask "is this safe?" — the resolution is a human decision (mark Safe, At Risk, Acknowledged). The fix you write is *the evidence the user needs to make that call*, not a code patch.

## When to use this skill

- ✅ After implementing a feature, before opening a PR ("is this Sonar-compliant?")
- ✅ When CI shows a failed Sonar gate and the user wants the findings explained locally before pushing again
- ✅ Before merging a long-lived branch back to main — final gate check
- ✅ Sanity check after rebasing onto main, to catch newly-applied rules

## When NOT to use this skill

- ❌ Repo isn't set up for Sonar (no `sonar-project.properties`). Run `sonar-onboard` first.
- ❌ User wants a code review broader than Sonar's catalog covers (architecture, idiomatic concerns, test-design). Use `devils-advocate` instead — different lens.
- ❌ User wants to fix the *whole codebase*'s Sonar debt. This skill is per-change; for a debt-paydown plan, query the Sonar UI directly.
- ❌ Repo only has linters (ESLint, Pylint, golangci-lint) and no Sonar. Different tool, different catalog — running this skill would produce nothing.
- ❌ Repo isn't wired to *either* SonarQube server or SonarCloud — no `sonar-project.properties` means there's nothing to scan against. Run `sonar-onboard` first.

## Anti-patterns to avoid

- ❌ **Guessing the gate result.** Always wait for the actual scan + API call. A "should pass" prediction without the scan is the worst possible output — it builds false confidence.
- ❌ **Reporting issues from untouched files.** The user opened a PR for one feature; flooding them with debt from other files is noise. Scope strictly to changed files; pre-existing-in-touched-files go in the FYI section.
- ❌ **Translating rule IDs into prose.** Keep `javascript:S2228` literal — that's the click-through key. ❌ "Use of console logging" ✅ "[javascript:S2228] Use of console logging".
- ❌ **Suggesting `// NOSONAR` as the default fix.** That's "make the linter shut up", not compliance. Reserve for documented exceptions with a comment explaining why.
- ❌ **Auto-fixing the code.** This skill produces a *report*. The user (or another agent / skill) decides what to change. Auto-fixes hide the learning and the audit trail.
- ❌ **Hiding the FAIL.** If the gate fails, lead with FAIL. Don't bury it under "but here's what's good" — the user opened this skill to know whether they can merge.
- ❌ **Treating security hotspots as bugs.** Hotspots are *review-required*; the resolution is human judgment. Show the evidence, then ask the user to mark Safe / At Risk / Acknowledged — don't patch them silently.
