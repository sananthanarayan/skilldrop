# sonar-review — reference

Long-form material that doesn't belong in `SKILL.md`.

## SonarQube server vs SonarCloud — what changes for this skill

Almost nothing. The API endpoints used here (`/api/qualitygates/project_status`, `/api/issues/search`, `/api/hotspots/search`) are identical in shape on both, authenticated the same way (`Authorization: Bearer $SONAR_TOKEN` or basic auth with the token as username). Only the host differs:

| Mode | `$SONAR_HOST` |
|---|---|
| SonarQube server | `$SONAR_HOST_URL` (from env) |
| SonarCloud | `https://sonarcloud.io` (fixed) |

Mode is detected from `sonar-project.properties` — presence of `sonar.organization=<key>` means SonarCloud; absence means server. Don't ask the user; the properties file is canonical.

Two behaviors that *do* differ:

- **Branch analysis** — SonarCloud supports branch + PR analysis on all tiers. SonarQube Community Edition does not. If you set `sonar.branch.name` and the server returns `License not valid for branch analysis`, you're on Community Edition. Re-run without the flag; the scan will overwrite the default-branch history, which is acceptable for a local pre-merge check but not for CI.
- **PR decoration** — SonarCloud auto-decorates the PR with findings if `GITHUB_TOKEN` is in the workflow env. Self-hosted needs ALM integration set up server-side. This skill doesn't touch PR decoration, but if the user asks why findings aren't appearing on the PR even though the scan ran, it's usually this.

## SonarQube API shapes you'll parse

### `/api/qualitygates/project_status`

```json
{
  "projectStatus": {
    "status": "ERROR",  // or "OK"
    "conditions": [
      {
        "status": "ERROR",
        "metricKey": "new_coverage",
        "comparator": "LT",
        "errorThreshold": "80",
        "actualValue": "71.4"
      },
      {
        "status": "OK",
        "metricKey": "new_bugs",
        "comparator": "GT",
        "errorThreshold": "0",
        "actualValue": "0"
      }
    ]
  }
}
```

`status` is the gate verdict (`OK` / `ERROR`). `conditions` is the per-rule breakdown — list the `ERROR` ones in the report's gate-conditions table.

### `/api/issues/search`

```json
{
  "issues": [
    {
      "key": "AYz1...",
      "rule": "javascript:S2259",
      "severity": "CRITICAL",
      "type": "BUG",
      "component": "myorg_payments:src/api/checkout.ts",
      "line": 47,
      "message": "Refactor this code to not use null dereference.",
      "status": "OPEN",
      "tags": ["cwe"]
    }
  ],
  "paging": { "total": 42, "pageIndex": 1, "pageSize": 100 }
}
```

`component` includes the project key prefix — strip it to get the file path. `severity` is one of `BLOCKER` / `CRITICAL` / `MAJOR` / `MINOR` / `INFO`. `type` is one of `BUG` / `VULNERABILITY` / `CODE_SMELL` (hotspots come from a different endpoint).

### `/api/hotspots/search`

```json
{
  "hotspots": [
    {
      "key": "AYz2...",
      "component": "myorg_payments:src/jobs/export.ts",
      "line": 28,
      "ruleKey": "javascript:S2076",
      "vulnerabilityProbability": "HIGH",  // HIGH / MEDIUM / LOW — maps to review priority
      "status": "TO_REVIEW",                // TO_REVIEW / REVIEWED
      "message": "Make sure that executing this OS command is safe here."
    }
  ]
}
```

Hotspots **don't** appear in `/api/issues/search`. Forgetting to call this endpoint silently drops the security-hotspot lens.

## Maven / Gradle / dotnet wrappers

If `sonar-project.properties` references the standalone scanner but the project has `pom.xml`, `build.gradle`, or a `.sln`, prefer the language-native wrapper — it hooks into the compile step and produces better analysis:

| Project type | Command |
|---|---|
| Maven | `mvn -B verify sonar:sonar -Dsonar.host.url=$SONAR_HOST_URL -Dsonar.token=$SONAR_TOKEN` |
| Gradle | `./gradlew build sonar -Dsonar.host.url=$SONAR_HOST_URL -Dsonar.token=$SONAR_TOKEN` |
| .NET | `dotnet sonarscanner begin /k:"<key>" /d:sonar.host.url=$SONAR_HOST_URL /d:sonar.token=$SONAR_TOKEN` → `dotnet build` → `dotnet sonarscanner end /d:sonar.token=$SONAR_TOKEN` |

The standalone `sonar-scanner` still works for these but won't see compile-time information (type resolution, framework attributes). Findings will be shallower.

## Scoping to PR diff

The skill scopes the **report** to changed files, not the scan itself. To compute the changed files:

```bash
# vs origin/main (most PRs)
git diff --name-only origin/main...HEAD

# vs the previous commit (just-pushed work)
git diff --name-only HEAD~1
```

When filtering issues, normalize the Sonar `component` field (`<projectKey>:<path>`) against your diff list. Strip the project-key prefix; compare paths.

**Don't filter the scan**. `sonar-scanner` analyzes the whole project because cross-file analysis (call graphs, import resolution) requires it. You filter the *findings* on the way out.

## Running against the SonarQube server with `branch` analysis

The SonarQube Developer Edition+ supports branch analysis natively — pass `-Dsonar.branch.name=<branch>`. Community Edition does **not**. If the Sonar server returns:

```
ERROR: License not valid for branch analysis. Branches will not be analyzed.
```

… the project is on Community Edition. Workarounds:

- Use the **`sonar.projectVersion`** trick — set `projectVersion=<branch>` to get separate histories per branch (crude but works on CE).
- Scan only on merge to `main` (PR-time scanning unavailable on CE).
- Upgrade to Developer Edition if branch analysis is required.

Document the edition limitation in the report — don't pretend the missing branch view is a configuration issue.

## Polling the scan task

`sonar-scanner` returns once it uploads to the server, but the gate isn't computed until the server processes the task. After the scanner finishes:

```bash
TASK_URL=$(grep '^ceTaskUrl=' .scannerwork/report-task.txt | cut -d= -f2-)

# Poll until status=SUCCESS (or FAILED)
while true; do
  STATUS=$(curl -s -u "$SONAR_TOKEN:" "$TASK_URL" | jq -r '.task.status')
  case "$STATUS" in
    SUCCESS) break ;;
    FAILED|CANCELED) echo "Scan task failed: $STATUS"; exit 1 ;;
    *) sleep 5 ;;
  esac
done
```

Skipping this means the gate API returns stale data from the *previous* scan, not this one. Always poll.

## Common false positives worth knowing

| Rule | Common false positive | What to do |
|---|---|---|
| `javascript:S2068` (hard-coded password) | Variable named `password` in a Zod/Joi schema definition | Mark `false positive` in Sonar UI |
| `python:S5689` (use of `eval`) | `ast.literal_eval` (safe) flagged alongside `eval` | Confirm `literal_eval`, ignore |
| `java:S3776` (cognitive complexity) | Big `switch` over an enum | Extract per-case handlers if it improves things; otherwise dispute |
| `csharpsquid:S1135` (TODO comment) | TODOs intentionally tracked in code | Roll up the count, don't list each |

These are dispositions to suggest, **not** to apply silently. The user marks them in Sonar UI; you surface them in the report so they know which to look at.
