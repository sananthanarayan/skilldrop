---
name: sonar-onboard
description: Scaffold a repo for Sonar compliance — supports both **SonarQube server** (self-hosted) and **SonarCloud** (SaaS), user picks at setup time. Generates `sonar-project.properties` with language-correct source/test/coverage paths, a CI workflow that runs the scanner on every push and PR and blocks merge on quality-gate failure, and a README snippet documenting the gate. One-shot setup; pair with `sonar-review` for per-change feedback. Use when the user says "set up Sonar", "add SonarQube to this repo", "wire up SonarCloud", "set up the quality gate", or asks to make a project Sonar-compliant for the first time.
---

# sonar-onboard

Scaffolds the artifacts a repo needs to become Sonar-compliant: a `sonar-project.properties` keyed to the project's actual language and layout, a CI workflow that runs the scanner and enforces the quality gate, and a README block so the next contributor knows what the gate means and how to run a scan locally.

This is a **one-shot setup skill**. For per-change feedback after the repo is onboarded, use [`sonar-review`](../sonar-review/SKILL.md).

Supports both deployment models — the user picks one:

| Mode | When it's right | Host | Key extras |
|---|---|---|---|
| **SonarQube server** | Self-hosted, on-prem or in own VPC. Enterprise / regulated orgs. | `https://sonar.<company>.com` (set per-org) | Project token + host URL |
| **SonarCloud** | SaaS, hosted by SonarSource. Faster setup, no infra. | `https://sonarcloud.io` (fixed) | Project token + **organization key** |

The choice changes three things: the properties file (SonarCloud needs `sonar.organization`), the GitHub Actions step (different action), and the secrets the user must add. Everything else is identical.

## How to respond

1. **Ask which mode** if the user hasn't said — it's the first question. One question, not two:

   > Which Sonar are you using — **SonarQube server** (self-hosted) or **SonarCloud** (SaaS at sonarcloud.io)?

   If they describe the host URL, infer: anything matching `sonarcloud.io` ⇒ SonarCloud; anything else ⇒ SonarQube server. Don't ask twice.

2. **Collect the inputs.** Ask for whichever are missing. Cap at two more clarifying questions per turn; pick defaults for the rest and call them out:

   | Input | Required for | Default if not given |
   |---|---|---|
   | **Project key** (e.g. `myorg_payments-api`) | both | `<repo-name>` (derive from `git remote get-url origin`) |
   | **Organization key** (SonarCloud only, e.g. `my-org`) | SonarCloud | Required — ask if missing |
   | **SonarQube host URL** (e.g. `https://sonar.company.com`) | SonarQube server | Required — ask if missing |
   | **Primary language(s)** | both | Detect from repo (see step 3) |
   | **CI system** | both | GitHub Actions (emit `gitlab-ci`/`jenkins`/`azure-pipelines` only if user names it) |
   | **Coverage tool** | both | Detect from language (see step 4) |

3. **Detect language(s)** from the working tree — don't ask if a probe will tell you:

   | Marker file | Language | Default source dir |
   |---|---|---|
   | `package.json` | JavaScript / TypeScript | `src` |
   | `pom.xml` | Java (Maven) | `src/main/java` |
   | `build.gradle` / `build.gradle.kts` | Java / Kotlin (Gradle) | `src/main/java` or `src/main/kotlin` |
   | `requirements.txt` / `pyproject.toml` / `setup.py` | Python | top-level package dir or `src` |
   | `go.mod` | Go | repo root |
   | `*.csproj` / `*.sln` | C# / .NET | project dirs |
   | `Cargo.toml` | Rust | `src` |
   | `composer.json` | PHP | `src` |
   | `Gemfile` | Ruby | `lib` and `app` |

   Multi-language is normal (e.g. TypeScript frontend + Python backend) — set `sonar.sources` to a comma-separated list and emit one combined `sonar-project.properties`. Don't generate one file per language.

4. **Pick the coverage report path** based on language. These are the formats Sonar's importers expect:

   | Language | Coverage report | Sonar property |
   |---|---|---|
   | JS / TS | `coverage/lcov.info` (Jest, Vitest default) | `sonar.javascript.lcov.reportPaths` |
   | Java (Maven) | `target/site/jacoco/jacoco.xml` | `sonar.coverage.jacoco.xmlReportPaths` |
   | Java (Gradle) | `build/reports/jacoco/test/jacocoTestReport.xml` | `sonar.coverage.jacoco.xmlReportPaths` |
   | Python | `coverage.xml` (`pytest-cov --cov-report=xml`) | `sonar.python.coverage.reportPaths` |
   | Go | `coverage.out` | `sonar.go.coverage.reportPaths` |
   | C# | `coverage.opencover.xml` (coverlet) | `sonar.cs.opencover.reportsPaths` |

   If the user has no coverage tool today, **don't fabricate a report path**. Omit the coverage property and add a `# TODO` comment in the properties file pointing them at the right one.

5. **Generate `sonar-project.properties`** using [`templates/sonar-project.properties.tmpl`](templates/sonar-project.properties.tmpl). Fill placeholders; remove blocks that don't apply.

   **For SonarCloud**, add this line (immediately after `sonar.projectKey`):
   ```
   sonar.organization={{ORG_KEY}}
   ```
   The organization key is mandatory for SonarCloud and rejected by SonarQube server — emit it for one and not the other.

   **Exclusions** — add these by default; they save the next contributor from a noisy first scan:
   ```
   sonar.exclusions=**/node_modules/**,**/dist/**,**/build/**,**/.next/**,**/__pycache__/**,**/*.generated.*,**/vendor/**,**/migrations/**
   sonar.test.exclusions=**/*.test.*,**/*.spec.*,**/test/**,**/tests/**
   sonar.coverage.exclusions=**/*.test.*,**/*.spec.*,**/test/**,**/tests/**,**/*.stories.*,**/index.{js,ts}
   ```
   Trim language-irrelevant entries (e.g. drop `__pycache__` for a pure-JS repo).

6. **Generate the CI workflow.** Default is GitHub Actions. Pick the template by mode:

   | Mode | Template | Scan action | Gate action |
   |---|---|---|---|
   | SonarQube server | [`templates/github-actions-sonar-server.yml.tmpl`](templates/github-actions-sonar-server.yml.tmpl) | `sonarsource/sonarqube-scan-action@v3` | `sonarsource/sonarqube-quality-gate-action@master` |
   | SonarCloud | [`templates/github-actions-sonarcloud.yml.tmpl`](templates/github-actions-sonarcloud.yml.tmpl) | `SonarSource/sonarcloud-github-action@master` | (built into scan action — `pollingTimeoutSec` controls wait) |

   Both must:
   - Trigger on `push` to default branch **and** `pull_request` (Sonar needs the PR event to comment on the PR).
   - Use `actions/checkout@v4` with `fetch-depth: 0` (Sonar needs full history to attribute blame).
   - Run the project's build + test + coverage **before** the scanner, otherwise coverage is empty.
   - Reference `SONAR_TOKEN` from GitHub Secrets — never inline.

   Mode-specific:
   - **Server** also references `SONAR_HOST_URL` from Secrets, and runs a separate `sonarqube-quality-gate-action` step so the job fails on gate failure.
   - **SonarCloud** doesn't need `SONAR_HOST_URL` (the action defaults to `https://sonarcloud.io`), and references `GITHUB_TOKEN` for PR decoration.

   For GitLab / Jenkins / Azure DevOps, see [`reference.md`](reference.md) — only emit those if the user names them.

7. **Generate the README snippet** using [`templates/readme-snippet.md`](templates/readme-snippet.md). Drop it under a `## Code quality` heading. It documents: what the gate enforces, the two required secrets, the local-scan command, and where to read findings (Sonar UI link).

8. **List the secrets the user must add manually.** End your response with this exact block — the skill cannot set secrets and shouldn't pretend it can. The steps differ by mode:

   **SonarQube server:**
   ```
   Manual steps you must do before the workflow runs green:
   1. Create a SonarQube project at <SONAR_HOST_URL>/projects/create with key `<project-key>`.
   2. Generate a project token (My Account → Security → Generate Token).
   3. Add GitHub Secret `SONAR_TOKEN` with the token value.
   4. Add GitHub Secret `SONAR_HOST_URL` with `<SONAR_HOST_URL>`.
   5. (Optional) Tighten the Quality Gate in Sonar UI — defaults are listed in the README snippet.
   ```

   **SonarCloud:**
   ```
   Manual steps you must do before the workflow runs green:
   1. Sign in at https://sonarcloud.io with the GitHub account that owns this repo.
   2. Create / import the project: + → Analyze new project → pick the repo. Confirm organization is `<org-key>` and project key is `<project-key>`.
   3. Disable "Automatic Analysis" on the project (Administration → Analysis Method) — the CI-driven scan and Automatic Analysis cannot both run.
   4. Generate a token (My Account → Security → Generate Token).
   5. Add GitHub Secret `SONAR_TOKEN` with the token value.
   6. (Optional) Tighten the Quality Gate in SonarCloud UI — defaults are listed in the README snippet.
   ```

## Useful references in this skill

- [`templates/sonar-project.properties.tmpl`](templates/sonar-project.properties.tmpl) — properties file skeleton (works for both modes; `sonar.organization` line is SonarCloud-only)
- [`templates/github-actions-sonar-server.yml.tmpl`](templates/github-actions-sonar-server.yml.tmpl) — CI workflow for self-hosted SonarQube
- [`templates/github-actions-sonarcloud.yml.tmpl`](templates/github-actions-sonarcloud.yml.tmpl) — CI workflow for SonarCloud
- [`templates/readme-snippet.md`](templates/readme-snippet.md) — README section for the gate (mode-aware placeholders)
- [`reference.md`](reference.md) — GitLab / Jenkins / Azure DevOps variants, quality-gate tuning, monorepo guidance, server vs cloud differences

## Quality bar

- **Properties file is keyed to the actual repo.** `sonar.projectKey`, `sonar.sources`, `sonar.tests`, and the coverage path must reflect what's on disk — not a generic example. A properties file that scans the wrong directories produces a green gate that means nothing.
- **The workflow blocks merge on gate failure.** A scan that runs but doesn't fail PRs is decoration. The `sonarqube-quality-gate-action` step is non-negotiable.
- **Coverage path exists or is marked TODO.** Pointing at a coverage file that the test step never produces gives Sonar 0% coverage and a false-failing gate. Either wire it up end-to-end or leave it explicit.
- **`fetch-depth: 0` in checkout.** Shallow clones break Sonar's new-code-period detection. The first scan will look fine; the next ten PRs will mis-attribute issues.
- **Secrets are referenced, never inlined.** No raw tokens or URLs in committed files. The token belongs in GitHub Secrets; the URL too, even though it's not technically secret — it keeps fork PRs from leaking the host.
- **README snippet tells the next contributor what the gate enforces.** "Sonar must pass" is not enough — list the conditions (no new bugs, no new vulnerabilities, coverage on new code ≥ X%, duplication ≤ Y%).

## When to use this skill

- ✅ First-time Sonar setup on a repo (server or cloud)
- ✅ Migrating between modes — SonarCloud → self-hosted (or vice versa). Re-scaffold with the new mode; remember to switch templates *and* the properties file.
- ✅ Adding Sonar to a fork or a new service in a monorepo (one properties file per module — see `reference.md`)
- ✅ Replacing an ad-hoc, locally-run scanner setup with a gate-enforcing CI workflow

## When NOT to use this skill

- ❌ Repo already has a working `sonar-project.properties` and a CI workflow that runs the scanner. Use `sonar-review` for per-change feedback instead.
- ❌ User wants to disable rules or relax the gate to make a failing scan pass. That's a code-quality conversation, not a setup task — push back.
- ❌ User wants language-specific deep config (custom rule profiles, Sonar plugins, branch analysis tuning). Out of scope; point at [`reference.md`](reference.md) and the Sonar docs.
- ❌ User wants both SonarQube server *and* SonarCloud scanning the same repo. Pick one — running both means two gates, two histories, and two answers to "did the build pass?".

## Anti-patterns to avoid

- ❌ **Emitting `sonar.organization` for SonarQube server.** It's SonarCloud-only and the server rejects it. Conversely: omitting it for SonarCloud breaks the scan.
- ❌ **Emitting a `sonar.login=...` line.** Deprecated since Sonar 10. Use `SONAR_TOKEN` env var, which both scan actions read automatically.
- ❌ **Hard-coding the host URL in the properties file** (server mode). It belongs in CI env / the scan action input, so forks and local runs don't ship someone else's Sonar.
- ❌ **Forgetting to disable SonarCloud's Automatic Analysis.** The CI scan and Automatic Analysis can't coexist; SonarCloud will fail one of them. The Manual Steps block must include this — it's the #1 cause of "scan ran but didn't update".
- ❌ **Generating multiple `sonar-project.properties` files for a multi-language single project.** One project = one properties file with comma-separated `sonar.sources`.
- ❌ **Skipping `pull_request` trigger.** A scan that only runs on `main` finds problems after they're merged — defeats the purpose.
- ❌ **Inventing a coverage path because "Sonar wants one".** If the project doesn't generate coverage, omit the property and TODO it. A path that points at nothing produces a misleading gate.
- ❌ **Recommending the user disable rules to pass the gate.** The gate exists to surface real issues. Suggest fixes or scope the gate to "new code" rather than turning rules off.
- ❌ **Burying the manual steps.** The "Manual steps you must do" block is the most important output — the workflow can't run green without it. Don't summarize it; print it verbatim.
