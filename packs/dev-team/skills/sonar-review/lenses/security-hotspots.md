# Lens 3 — Security Hotspots

Hotspots are the lens most agents get wrong. They are **not** vulnerabilities. They are **security-sensitive code patterns Sonar can't auto-decide are safe** — the resolution is a *human security review*, recorded in Sonar as **Safe**, **At Risk**, or **Acknowledged**.

Hotspots come from a **different API** (`/api/hotspots/search`) than Issues. The quality gate counts unresolved hotspots — so an un-reviewed hotspot fails the gate even if the code is secure.

## What you're looking at

| Family | Example IDs | What it catches |
|---|---|---|
| Cryptographic operations | `S4426`, `S2278` | Use of crypto APIs (could be configured weakly) |
| Random number generation | `S2245` | `Math.random()` / `Random` — fine for UI, dangerous for tokens |
| Regex DoS | `S5852` | Catastrophic backtracking patterns |
| File permissions | `S2612` | World-writable file creation |
| Authentication / authorization | `S5332` | TLS disabled, `verify=False`, `--insecure` |
| User-controlled file paths | `S2083` (sometimes Hotspot) | Where validation might be present |
| Hardcoded IPs / CIDR | `S1313` | Could be a test fixture, could be a backdoor |
| Cookie / session config | `S2092`, `S3330` | Missing flags Sonar can't verify in context |
| HTTP method overrides | `S5122` | CORS / `_method` rewriting |
| Command execution | `S4721` | `exec`-shaped calls (may be safe with constants) |

## How to phrase each Hotspot finding

This lens has **five** parts, not four — because the artifact you produce isn't "fix this", it's "evidence for the user to make a decision":

1. **Where** — `file:line` + the sensitive call. Quote 5–15 chars.
2. **Rule + category** — `[HOTSPOT · javascript:S2245] Pseudorandom generator use`.
3. **Why it's flagged** — what *category* of risk Sonar is asking about. ✅ "`Math.random()` is fine for UI shuffling but unsafe for security tokens." ❌ "Insecure RNG."
4. **Evidence for review** — what *this codebase* tells you about whether the usage is actually risky. Quote the surrounding context:
   - Where does the value flow next? (logged? sent? stored? returned to user?)
   - Are there upstream guards? Quote them with `file:line`.
   - Is this test/dev-only code? Quote the file path or test scaffolding around it.
5. **Action** — name the **resolution the user should record in Sonar**, with the reasoning they should paste into the resolution comment:
   - **Safe** — quote the upstream guard or the non-security usage that makes it OK.
   - **At Risk** — name the path you can't rule out + the code fix.
   - **Acknowledged** — for known issues with a tracked follow-up. Include the ticket reference.

## Calibration

Hotspots don't carry the BLOCKER/CRITICAL/MAJOR severities issues do — they have a **review priority** (`HIGH`/`MEDIUM`/`LOW`) and a **status** (`TO_REVIEW`/`REVIEWED`). Map to your report:

| Hotspot priority | Report marker |
|---|---|
| HIGH | 🟧 |
| MEDIUM | 🟨 |
| LOW | ⚪ |

Group hotspots in their own section — don't intermix with bugs/vulnerabilities. They're a different shape of finding.

## Anti-patterns when reporting Hotspots

- ❌ **Treating Hotspots like Vulnerabilities.** A Hotspot isn't a defect — it's a question. Reporting "fix this insecure RNG" when the value flows to a UI shuffle is wrong; the answer is "mark Safe with this evidence."
- ❌ **Recommending a code patch without naming the resolution.** A code patch alone doesn't clear the hotspot in Sonar — the user still needs to mark it Reviewed. Always include "and mark `<status>` in the Sonar UI with the evidence above".
- ❌ **Skipping the evidence step.** "Looks fine to me" isn't actionable. Quote the upstream guard or the test-only usage that lets the user click Safe with confidence.
- ❌ **Marking everything At Risk to be cautious.** If the evidence is "no upstream guard, flows to user output", say At Risk. If the evidence is "constant string from build config, never user-influenced", say Safe. Hedging defeats the workflow.
- ❌ **Forgetting that un-reviewed hotspots fail the gate.** Even a clearly-safe hotspot fails the gate until reviewed. Tell the user explicitly: "marking this Safe is what unblocks the gate — not a code change."
