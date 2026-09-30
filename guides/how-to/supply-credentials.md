---
title: Supply credentials to skills
summary: How to provide API keys and tokens to skills that declare env.required — covers local shells, CI environments, and enterprise secret managers.
kind: how-to
---

# Supply credentials to skills

Most skills need no credentials. Three skills in the catalogue declare environment variables:

| Skill | Variable | Required / Optional | Used for |
|---|---|---|---|
| `figma-diagrams` | `FIGMA_TOKEN` | Required | Figma REST API — reading file structure, posting comments |
| `sonar-review` | `SONAR_TOKEN` | Required | SonarQube/SonarCloud API — fetching issue and quality-gate data |
| `sonar-review` | `SONAR_HOST_URL` | Optional | SonarCloud by default; set to your self-hosted instance URL |
| `sonar-onboard` | `SONAR_HOST_URL` | Optional | Same as above |

If a skill's `env.required` variable is absent, the skill's script will error on startup and tell you exactly which variable is missing — it never silently produces wrong output.

## Local development

Set the variable in your shell before launching Claude Code:

```bash
export FIGMA_TOKEN=<your-figma-personal-access-token>
export SONAR_TOKEN=<your-sonar-token>
export SONAR_HOST_URL=https://sonar.your-company.com  # only if self-hosted
```

Variables set in the shell before Claude Code starts are available to the agent when it runs skill scripts.

Alternatively, add them to `~/.claude/settings.json` under the `env` key so they are always present regardless of how Claude Code is launched:

```json
{
  "env": {
    "FIGMA_TOKEN": "<your-figma-personal-access-token>",
    "SONAR_TOKEN": "<your-sonar-token>"
  }
}
```

## CI/CD (GitHub Actions)

Store secrets in your repo's Settings → Secrets and variables → Actions. Then pass them to the step:

```yaml
- name: Run sonar-review skill
  env:
    SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
    SONAR_HOST_URL: ${{ secrets.SONAR_HOST_URL }}
  run: |
    # the skill script reads these from the environment
    python3 .claude/skills/sonar-review/scripts/review.py
```

Never hard-code tokens in workflow files — they end up in git history.

## Enterprise secret managers

The pattern is to export the secret to the process environment before running the skill. The skill reads it from there and never sees the manager directly.

**HashiCorp Vault:**

```bash
export FIGMA_TOKEN=$(vault kv get -field=value secret/ci/figma-token)
```

**AWS Secrets Manager:**

```bash
export FIGMA_TOKEN=$(aws secretsmanager get-secret-value \
  --secret-id prod/figma-token --query SecretString --output text)
```

**Azure Key Vault:**

```bash
export FIGMA_TOKEN=$(az keyvault secret show \
  --vault-name your-vault --name figma-token --query value -o tsv)
```

Run these lines before launching Claude Code or before the CI step that invokes the skill.

## Getting the tokens

- **FIGMA_TOKEN**: Figma → Account Settings → Personal access tokens → Generate new token. Grant "Read" scope for `figma-diagrams` reads; "Write comments" if you use the post-comment action.
- **SONAR_TOKEN**: SonarCloud → My Account → Security → Generate token. For SonarQube: Administration → Security → Users → your user → Tokens.
- **SONAR_HOST_URL**: the base URL of your SonarQube instance, e.g. `https://sonar.your-company.com`. Omit for SonarCloud.
