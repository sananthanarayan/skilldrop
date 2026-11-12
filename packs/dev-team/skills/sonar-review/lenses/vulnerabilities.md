# Lens 2 — Vulnerabilities

Sonar's **Vulnerability** category is code where **Sonar is confident an attacker can exploit it**: injection, weak crypto, hard-coded secrets, broken auth flows, unsafe deserialization. Different from **Hotspots** (lens 3) — Hotspots are "this *could* be unsafe, a human needs to look"; Vulnerabilities are "this *is* unsafe by the catalog's definition".

Every Vulnerability on new code is a **gate failure** under the default Sonar way. Treat as merge-blocking.

## What you're looking at

Pull the issues list, filter to `type=VULNERABILITY`, intersect with changed files. Common rule families:

| Family | Example IDs | What it catches |
|---|---|---|
| SQL injection | `javascript:S3649`, `java:S3649`, `python:S3649` | String-concatenated queries |
| Command injection | `S2076`, `S4036` | `exec(\`tar ${user}\`)`, `Runtime.exec(userInput)` |
| Path traversal | `S2083`, `S6549` | `fs.readFile(userInput)` without normalization |
| XSS | `javascript:S5247`, `S5131` | `innerHTML = userInput`, unescaped template output |
| SSRF | `S5144` | HTTP client URL built from user input |
| Hard-coded secrets | `S6418`, `S2068` | API keys, passwords, tokens in source |
| Weak crypto | `S2278`, `S5547`, `S4790` | MD5/SHA1 for auth, ECB mode, deprecated TLS |
| Insecure cookie | `S2092`, `S3330` | `httpOnly: false`, missing `secure` flag |
| Open redirect | `javascript:S5146` | `res.redirect(userInput)` |
| Unsafe deserialization | `S5135` | `pickle.loads(network_bytes)`, Java `ObjectInputStream` |
| Permissive CORS | `S5122` | `Access-Control-Allow-Origin: *` with credentials |

Every Vulnerability rule is tagged with **CWE** and (where applicable) **OWASP Top 10** identifiers — surface these in the finding so the user can map to compliance frameworks.

## How to phrase each finding

1. **Where** — `file:line` + the offending expression. Quote enough to make the data flow obvious.
2. **Rule + category + standards tags** — `[VULNERABILITY · javascriptsecurity:S3649 · CWE-89 · OWASP A03:2021] SQL injection`.
3. **Why it matters** — describe the **exploit path**, not the rule. ✅ "`userId` flows from `req.params.id` into the SQL string at line 42 without escaping — an attacker can send `1 OR 1=1` and read every row of the table." ❌ "Possible SQL injection."
4. **Fix** — concrete and **the right one**:
   - SQL injection → parameterized query / prepared statement, with a code snippet using the project's existing DB client. Quote the right call from elsewhere in the codebase if available.
   - Command injection → `execFile(cmd, [args])` not `exec(cmd + args)`; never `shell: true` with user data.
   - XSS → contextual escaping (text vs attribute vs URL vs JS), or the framework's safe primitive (`.textContent` not `.innerHTML`; `{}` not `{{{}}}`).
   - Hard-coded secret → move to env/secret manager, **rotate the leaked value**, and call out the rotation explicitly — finding it in source means it was committed and is in git history.
   - Weak crypto → name the replacement algorithm (e.g. `SHA-256 + HMAC`, `bcrypt/argon2`, `AES-256-GCM`).

## Calibration

- **BLOCKER vulnerability** — direct injection / hard-coded prod credential / known-broken crypto on auth. Stop the merge; in some cases stop the deploy (rotate creds, audit access).
- **CRITICAL vulnerability** — exploit requires a slightly less trivial path (chained, requires auth, narrow window). Fix before merge.
- **MAJOR vulnerability** — defense-in-depth issue (missing flag, weak default). Fix before merge if reasonable.

Do not down-grade these. If you think Sonar is wrong, mark it for the user to dispute via the Sonar UI (`Resolve as won't fix` / `false positive`) — don't silently drop it from the report.

## Anti-patterns when reporting Vulnerabilities

- ❌ Suggesting input validation as the fix for injection. Validation is defense in depth; **parameterization** is the fix. ❌ "Validate the user ID looks like a number." ✅ "Use `db.query('SELECT * FROM users WHERE id = $1', [userId])` — never concatenate."
- ❌ Forgetting the rotation step on a leaked secret. If a key was in source, it leaked; "remove the line" without "rotate the value" leaves the exposure live.
- ❌ Listing the rule's CWE without using it. The CWE tag is for the user's report, not your decoration — include it so they can answer "is this our SOC 2 finding?".
- ❌ Recommending the user mark it "won't fix" to pass the gate. The gate is the point. If it's truly a false positive, the resolution path is via the Sonar UI's `false positive` workflow, with a comment — not a CI-bypass.
