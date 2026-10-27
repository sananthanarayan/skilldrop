# sonar-onboard — reference

Long-form material that doesn't belong in `SKILL.md`.

## SonarQube server vs SonarCloud — what actually differs

The user picks one at setup. The differences are smaller than the marketing suggests, but the ones that matter are:

| Aspect | SonarQube server | SonarCloud |
|---|---|---|
| Host URL | Set per-org (e.g. `sonar.company.com`) | Fixed at `https://sonarcloud.io` |
| `sonar.organization` in properties | **Must not** be present | **Must** be present |
| GitHub Action | `sonarsource/sonarqube-scan-action@v3` + separate gate action | `SonarSource/sonarcloud-github-action@master` (single step) |
| Quality-gate action | `sonarsource/sonarqube-quality-gate-action@master` | Built into the scan action; separate action also works |
| GitHub Secrets | `SONAR_TOKEN`, `SONAR_HOST_URL` | `SONAR_TOKEN` only (host is implicit) |
| Branch analysis | Developer Edition+ only (Community Edition: no branches) | Included on all SonarCloud tiers |
| PR decoration | Needs ALM integration set up server-side | Auto-enabled when scan runs |
| Automatic Analysis | N/A | **Must be disabled** when using CI-driven scanning |
| Pricing | Per-instance license | Per-LoC subscription, free for open-source |
| Where the data lives | Your infra | SonarSource's (EU / US regions available) |

Two failure modes are mode-specific and worth surfacing:

- **SonarCloud + Automatic Analysis** — if both Automatic Analysis and the CI scan are enabled, SonarCloud rejects one (the second one to run). Symptom: random scan failures with "Project already analyzed". Fix: disable Automatic Analysis under Administration → Analysis Method.
- **SonarQube server + Community Edition + branch scanning** — Community Edition has no branch analysis; setting `sonar.branch.name` makes the scanner emit a license warning and fall back to scanning as the default branch (so feature-branch PRs overwrite `main`'s history). Fix: either upgrade to Developer Edition, or remove the `branch.name` line and scan only on merge.

## Non-GitHub CI variants

Only emit these if the user explicitly names the CI system. Defaults to GitHub Actions.

### GitLab CI

```yaml
sonarqube-check:
  image:
    name: sonarsource/sonar-scanner-cli:latest
    entrypoint: [""]
  variables:
    SONAR_USER_HOME: "${CI_PROJECT_DIR}/.sonar"
    GIT_DEPTH: "0"  # full history for blame
  cache:
    key: "${CI_JOB_NAME}"
    paths: [.sonar/cache]
  script:
    - sonar-scanner
  rules:
    - if: $CI_PIPELINE_SOURCE == 'merge_request_event'
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

GitLab passes `SONAR_TOKEN` and `SONAR_HOST_URL` via project-level CI/CD variables (Settings → CI/CD → Variables). Quality-gate enforcement requires the [GitLab MR decoration](https://docs.sonarsource.com/sonarqube/latest/devops-platform-integration/gitlab-integration/) setup on the Sonar side — the gate fails the pipeline automatically once decoration is wired.

### Jenkins

Requires the **SonarQube Scanner for Jenkins** plugin. In a `Jenkinsfile`:

```groovy
pipeline {
  agent any
  stages {
    stage('Build + Test') { steps { sh 'mvn -B verify' } }
    stage('SonarQube') {
      steps {
        withSonarQubeEnv('SonarQube-Server') {  // configured in Jenkins → System
          sh 'sonar-scanner'
        }
      }
    }
    stage('Quality Gate') {
      steps {
        timeout(time: 5, unit: 'MINUTES') {
          waitForQualityGate abortPipeline: true
        }
      }
    }
  }
}
```

`abortPipeline: true` is the equivalent of the GitHub `quality-gate-action` — without it, the gate is decorative.

### Azure DevOps

Install the **SonarQube extension** from the marketplace, then in `azure-pipelines.yml`:

```yaml
steps:
  - task: SonarQubePrepare@5
    inputs:
      SonarQube: 'SonarQube-ServiceConnection'
      scannerMode: 'CLI'
      configMode: 'file'
  - script: '<build + test + coverage commands here>'
  - task: SonarQubeAnalyze@5
  - task: SonarQubePublish@5
    inputs: { pollingTimeoutSec: '300' }
  - task: sonarcloud-buildbreaker@2  # NOTE: also works for SonarQube server
    inputs:
      SonarQube: 'SonarQube-ServiceConnection'
```

## Quality gate tuning

The skill emits the **Sonar way** default gate. Common project-specific adjustments:

- **Loosen coverage on new code** (default 80%) — for projects with hard-to-test integration code, drop to 60% and note the exception in the README.
- **Tighten duplication** (default 3%) — for libraries, 1% is reasonable; the dup gate catches copy-paste.
- **Add a "security review" condition** — for compliance-driven projects, require all security hotspots (not just new ones) to be reviewed.

Edit gates in Sonar UI: Quality Gates → `<gate-name>` → Conditions. Do **not** copy a gate config into source control — it lives server-side and applies per project.

## Monorepo guidance

For a monorepo with multiple deployable services, emit **one `sonar-project.properties` per service** at the service root, plus a root-level GitHub Actions workflow with a matrix:

```yaml
strategy:
  matrix:
    project:
      - path: services/payments
        key: myorg_payments
      - path: services/billing
        key: myorg_billing
steps:
  - uses: sonarsource/sonarqube-scan-action@v3
    with:
      projectBaseDir: ${{ matrix.project.path }}
    env:
      SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
      SONAR_HOST_URL: ${{ secrets.SONAR_HOST_URL }}
```

Each service is a separate Sonar project with its own gate and history. Don't try to put a multi-module config in one properties file — Sonar's "modules" feature is deprecated.

## Language-specific gotchas

- **TypeScript** — set `sonar.typescript.tsconfigPath=tsconfig.json` if the project uses path aliases; otherwise Sonar can't resolve imports and over-reports "unused" findings.
- **Java (Gradle)** — use the [Sonar Gradle plugin](https://docs.sonarsource.com/sonarqube/latest/analyzing-source-code/scanners/sonarscanner-for-gradle/) instead of the standalone scanner. It auto-detects sources, tests, and JaCoCo paths. The properties file then only needs `sonar.projectKey`.
- **Python** — Sonar imports `coverage.xml`, not `.coverage`. Run `coverage xml` (or `pytest-cov --cov-report=xml`) explicitly; the default `.coverage` binary is ignored.
- **Go** — coverage importer expects the raw `coverage.out` (Go's native format), not `cobertura` XML. Don't convert.
- **C# / .NET** — use the [`dotnet-sonarscanner`](https://docs.sonarsource.com/sonarqube/latest/analyzing-source-code/scanners/sonarscanner-for-dotnet/) tool, not the generic scanner. Wraps `dotnet build` so analysis hooks into the compile step.

## Why `fetch-depth: 0`

Shallow clones (the GitHub Actions default) ship only the last commit. Sonar uses git blame to attribute issues to authors and the new-code period to scope the gate. Without full history:

- All issues look like they were introduced in the latest commit → gate fails on existing debt.
- Blame UI in Sonar shows the wrong author for every line.
- "New code since previous version" becomes meaningless because the previous version isn't in the clone.

Always `fetch-depth: 0`. The extra clone time is a few seconds; the analytical correctness is worth it.
