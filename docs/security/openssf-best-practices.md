# OpenSSF Best Practices: answers for the "passing" badge

How to use this: sign in at [bestpractices.dev](https://www.bestpractices.dev) with the
repository owner's GitHub account, choose **Add project**, give
`https://github.com/sananthanarayan/skilldrop`, and answer each criterion from the table. Paste
the URL in the justification box. The answers were checked against the repository on
2026-10-21. Two criteria need a decision first; they are marked **decide**.

R = `https://github.com/sananthanarayan/skilldrop/blob/main`, S = `https://sananthanarayan.github.io/skilldrop`

## Basics

| Criterion | Answer | Evidence |
|---|---|---|
| `description_good` | Met | README opening; S/ (home) |
| `interact` | Met | README "Start in one command"; S/start/; [issue templates](https://github.com/sananthanarayan/skilldrop/issues/new/choose); R/CONTRIBUTING.md |
| `contribution` | Met | R/CONTRIBUTING.md: pull requests against `main`, the three lanes, the checks |
| `contribution_requirements` | Met | R/CONTRIBUTING.md "Before you open the PR"; R/AGENTS.md (golden rules, voice and tone, pre-commit checklist) |
| `floss_license` | Met | MIT OR Apache-2.0: R/LICENSE |
| `floss_license_osi` | Met | MIT and Apache-2.0 are both OSI-approved |
| `license_location` | Met | R/LICENSE, R/LICENSE-MIT, R/LICENSE-APACHE |
| `documentation_basics` | Met | S/docs/; R/README.md |
| `documentation_interface` | Met | S/docs/reference/install-options.html (every CLI command and flag); R/guides/reference/ci-action.md (the GitHub Action's inputs and outputs); R/contracts/ (JSON schemas for skills, packs, loops) |
| `sites_https` | Met | GitHub, GitHub Pages and the npm registry are HTTPS only |
| `discussion` | Met | GitHub Issues: public, searchable, linkable, no proprietary client. Add GitHub Discussions once it's turned on |
| `english` | Met | All documentation is in English |
| `maintained` | Met | Commits and releases weekly: R/CHANGELOG.md |

## Change control

| Criterion | Answer | Evidence |
|---|---|---|
| `repo_public` | Met | https://github.com/sananthanarayan/skilldrop |
| `repo_track` | Met | git history; every change lands by pull request |
| `repo_interim` | Met | Every merged pull request is in `main` between releases |
| `repo_distributed` | Met | git |
| `version_unique` | Met | Each release has its own version: R/package.json, R/CHANGELOG.md |
| `version_semver` | Met | SemVer: R/AGENTS.md "Releasing" |
| `version_tags` | Met | A `v<version>` tag for each release: https://github.com/sananthanarayan/skilldrop/tags |
| `release_notes` | Met | R/CHANGELOG.md; each GitHub Release's notes are its changelog entry |
| `release_notes_vulns` | N/A | No release has fixed a publicly known vulnerability with a CVE |

## Reporting

| Criterion | Answer | Evidence |
|---|---|---|
| `report_process` | Met | Issue templates for bugs and skill requests: https://github.com/sananthanarayan/skilldrop/issues/new/choose |
| `report_tracker` | Met | GitHub Issues |
| `report_responses` | Met | No bug reports have been filed yet. Note that in the justification, and revisit once reports arrive |
| `enhancement_responses` | Met | As above, none filed yet |
| `report_archive` | Met | https://github.com/sananthanarayan/skilldrop/issues?q=is%3Aissue |
| `vulnerability_report_process` | Met | R/SECURITY.md |
| `vulnerability_report_private` | Met | GitHub private vulnerability reporting: R/SECURITY.md links to it |
| `vulnerability_report_response` | N/A | No vulnerability reports in the last 6 months. SECURITY.md commits to acknowledging within 7 days |

## Quality

| Criterion | Answer | Evidence |
|---|---|---|
| `build` | Met | `npm pack` builds the package from source; CI publishes with provenance: R/.github/workflows/release.yml |
| `build_common_tools` | Met | npm and Python's standard library |
| `build_floss_tools` | Met | Node.js, npm and Python, all FLOSS |
| `test` | Met | `python3 -m unittest discover -s tests -t .` (the skill scripts), `node cli_smoke.js` (the CLI), `python3 validate.py`: R/CONTRIBUTING.md |
| `test_invocation` | Met | `unittest` discovery, the standard runner for Python |
| `test_most` | Met | Every skill script has a test file, enforced by validate.py: R/docs/rfcs/0060-skill-script-unit-tests.md |
| `test_continuous_integration` | Met | Linux, macOS and Windows on every pull request: R/.github/workflows/cli.yml |
| `test_policy` | Met | R/CONTRIBUTING.md: "A skill with a script needs its tests", enforced by validate.py |
| `tests_are_added` | Met | Pull request #82 added tests for every script; each new skill adds evals |
| `tests_documented_added` | Met | R/CONTRIBUTING.md "Before you open the PR"; R/.github/pull_request_template.md |
| `warnings` | Met | validate.py (repo lint), actionlint and zizmor (workflows), CodeQL (JavaScript and Python): R/.github/workflows/security.yml, R/.github/workflows/codeql.yml |
| `warnings_fixed` | Met | Each runs as a required check on every pull request; a finding blocks the merge |
| `warnings_strict` | Met | zizmor runs at medium severity; CodeQL runs its security-extended queries |

## Security

| Criterion | Answer | Evidence |
|---|---|---|
| `know_secure_design` | Met | **decide**: a statement about the maintainer, so answer it yourself. Supporting evidence: R/SECURITY.md, R/guides/reference/owasp-mapping.md, the scanner (`skilldrop scan`) and the agent-security skills |
| `know_common_errors` | Met | **decide**, as above. Evidence: R/guides/reference/owasp-mapping.md; the CodeQL and zizmor gates |
| `crypto_published` | N/A | The software implements no cryptographic protocol. SHA-256 is used only to fingerprint files, through Node's and Python's standard libraries |
| `crypto_call` | Met | Hashing uses Node's `crypto` and Python's `hashlib`; nothing is reimplemented |
| `crypto_floss` | N/A | No cryptography-dependent functionality |
| `crypto_keylength` | N/A | No keys are generated or used |
| `crypto_working` | N/A | No encryption |
| `crypto_weaknesses` | N/A | No encryption |
| `crypto_pfs` | N/A | No key agreement |
| `crypto_password_storage` | N/A | No passwords are stored |
| `crypto_random` | N/A | No keys or nonces are generated |
| `delivery_mitm` | Met | npm and GitHub, over HTTPS; npm checks each tarball's integrity hash |
| `delivery_unsigned` | Met | Releases carry npm provenance and a Sigstore-signed build attestation: R/SECURITY.md "Verifying a release" |
| `vulnerabilities_fixed_60_days` | Met | No open Dependabot or code-scanning vulnerability alerts. The package has no runtime dependencies |
| `vulnerabilities_critical_fixed` | Met | No critical vulnerabilities reported. Dependabot alerts are triaged as they arrive |
| `no_leaked_credentials` | Met | gitleaks scans the full history on every pull request (R/.github/workflows/security.yml). Also confirm secret scanning and push protection are on: Settings → Code security |

## Analysis

| Criterion | Answer | Evidence |
|---|---|---|
| `static_analysis` | Met | CodeQL on every pull request and on `main`: R/.github/workflows/codeql.yml |
| `static_analysis_common_vulnerabilities` | Met | CodeQL security queries; zizmor for GitHub Actions injection and permissions |
| `static_analysis_fixed` | Met | CodeQL findings are fixed before merge; for example the file-system race fixed in pull request #78 |
| `static_analysis_often` | Met | Every pull request and every push to `main` |
| `dynamic_analysis` | Met | Atheris fuzzing of the skill scripts' parsers in CI (RFC-0062). Answer Unmet until that pull request is merged |
| `dynamic_analysis_unsafe` | N/A | JavaScript and Python are memory-safe |
| `dynamic_analysis_enable_assertions` | Met | The fuzz targets assert each parser either succeeds or fails with its documented error |
| `dynamic_analysis_fixed` | Met | Crashes found by fuzzing are fixed before merge |

## After the badge

The project page gives a badge URL like `https://www.bestpractices.dev/projects/<id>/badge`.
Send the id, and it goes into the README beside the Scorecard badge. Scorecard picks it up on
its next weekly run.
