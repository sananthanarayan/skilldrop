## Code quality

This repo is gated by **{{SONAR_FLAVOR}}** ({{SONAR_FLAVOR}} = `SonarQube` for self-hosted, `SonarCloud` for SaaS). Every push to the default branch and every pull request runs a scan; the PR check fails if the quality gate fails.

**What the gate enforces** (Sonar default — tune in the Sonar UI per project):

| Condition | Threshold |
|---|---|
| New bugs | 0 |
| New vulnerabilities | 0 |
| New security hotspots reviewed | 100% |
| Coverage on new code | ≥ 80% |
| Duplicated lines on new code | ≤ 3% |
| Maintainability rating on new code | A |
| Reliability rating on new code | A |
| Security rating on new code | A |

The gate measures **new code** (since the previous version), not the whole codebase — so existing debt doesn't block your PR, but new debt does.

**Required GitHub secrets:**

<!-- For SonarQube server, keep both. For SonarCloud, keep only SONAR_TOKEN. -->
- `SONAR_TOKEN` — project token from {{SONAR_FLAVOR}} (My Account → Security → Generate Token)
- `SONAR_HOST_URL` — e.g. `https://sonar.company.com`  *(SonarQube server only; omit for SonarCloud)*

**Run a scan locally** (against the same {{SONAR_FLAVOR}} project):

```bash
export SONAR_TOKEN=<your-token>
# SonarQube server only:
export SONAR_HOST_URL=<your-sonar-host>
# SonarCloud: omit SONAR_HOST_URL — it defaults to https://sonarcloud.io
sonar-scanner
```

Findings appear at:
- **SonarQube server:** `${SONAR_HOST_URL}/dashboard?id=<project-key>`
- **SonarCloud:** `https://sonarcloud.io/dashboard?id=<project-key>`
