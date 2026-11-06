---
name: privacy-policy-check
description: Check a startup's privacy policy against what its app actually does — a script scans the code's dependencies, script tags and API calls for the services that receive users' data (analytics, ad pixels, session replay, error monitoring, payments, sign-in, email, support chat, AI model APIs, maps), then finds each one the policy doesn't disclose, each policy claim the code contradicts ("we never share your data" beside a Meta pixel), and the sections the policy lacks — and writes the paragraphs to add. Use when a founder asks "is our privacy policy accurate", "does our privacy policy cover everything we use", "check our privacy policy against the app", "we added analytics / OpenAI — do we need to update the policy", or before launch, an app-store review or a customer's security questionnaire.
---

# privacy-policy-check

Most startup privacy policies are written once, from a template, and then the product moves
on: an analytics SDK goes in for a growth experiment, a Meta pixel for an ad campaign, an AI
API for a new feature. Nobody updates the policy, and it now says things that aren't true.
That is what app-store reviewers, enterprise customers and regulators check first. A capable
agent asked to "review the privacy policy" reads the policy alone and judges its prose. This
skill reads the code: a script finds every service that receives users' data, and the policy is
checked against that list.

## How to respond

**These rules come before the steps and outrank them:**

- **Lead with what is untrue or missing, in a founder's words.** ✅ *"Your policy says you
  never share data with third parties, but the site loads the Meta pixel, which sends every
  visitor's page views to Meta for advertising. It also doesn't mention that journal entries
  go to OpenAI."* Never mention a script, this skill's name, or a path inside its folder.
- **Every service you name comes from the scan,** with where it was found (file and line, or
  the package). Never add a service from a guess about what apps like this use.
- **Give the fix as text to paste.** For each gap, the paragraph or sentence to add, written
  for this app, naming the service, what it receives and why. A founder without a lawyer can
  publish it today.
- **Say what the code can't show.** The scan sees what the code sends; it doesn't see what the
  founder's team does by hand (exporting a customer list to a spreadsheet), server-side data
  sharing configured in a dashboard, or which countries a vendor stores data in. List the
  questions that remain, in one short list.
- **Name what is worth a lawyer's hour, and only that.** One or two lines: children's data,
  health or financial data, selling data, or users in a jurisdiction with its own rules the
  founder plans to target. Never refuse, never open with a disclaimer.
- **Their policy is never overwritten.** An updated policy goes beside it under a plain name
  (`privacy-policy-updated.md`), only when asked for. Working files go in a private temporary
  folder (`mktemp -d`) and are deleted before replying.

1. **Find the code and the policy.** The code folder is usually the working directory; the
   policy is a file in it, a file the founder names, or text they paste (save a pasted policy
   in the private folder). With several apps (web and mobile), scan each folder.

2. **Run the scan.**

   ```bash
   work=$(mktemp -d 2>/dev/null || mktemp -d ./.work.XXXXXX)   # a private folder for this run only
   # Claude Code
   python3 "${CLAUDE_SKILL_DIR}/scripts/policy_scan.py" --code . --policy ./privacy-policy.md
   # Other IDEs (from the skill folder)
   python3 scripts/policy_scan.py --code ../../my-app --policy ../../my-app/privacy.md
   ```

   It reads dependency manifests (runtime dependencies only, not dev tools), and source and
   HTML for script tags, SDK calls and API hosts. Exit 0 means no failures, 1 means a failure,
   2 means a path can't be read. It **fails** when an advertising, analytics, session-replay or
   AI service isn't disclosed by name or kind, and when a policy claim contradicts the code. It
   **warns** when a processor that only runs the service (email delivery, payments, error
   monitoring) isn't mentioned, and when the policy lacks contact details, rights, retention,
   cookies (when the site sets them), international transfers, or children.

3. **Check what the scan flagged** in the code where it matters: a pixel that loads only
   after consent, an SDK imported but never initialised, an AI call that sends only
   metadata. Read the line it gave. Correct a finding only from what that code shows, and say
   so in the reply.

4. **Write the fixes** using [`reference.md`](reference.md): a paragraph per undisclosed
   service or kind, a replacement for each contradicted claim, and each missing section. Name
   the service, what it receives (page views, device data, the text the user types), and why.

5. **Reply in this order:**
   1. **The verdict** in one line, and what is untrue first: each contradiction, with the
      sentence from the policy and the code that contradicts it.
   2. **Services the policy doesn't disclose,** one line each: the service, where in the code,
      what it receives.
   3. **The text to add or replace,** ready to paste, under the policy heading it belongs in.
   4. **Missing sections,** with their text.
   5. **Questions the code can't answer,** as a short checklist for the founder.
   6. **What to have a lawyer look at,** one or two lines, only where it's earned.

**Non-interactive runs** (subagent, CI, headless): with code but no policy, list the services
and write a disclosure section for each, tagged as a draft. With neither code nor a policy,
emit `BLOCKED: need the app's code folder and its privacy policy`.

## Useful references in this skill

- [`reference.md`](reference.md) — what each kind of service receives, disclosure wording for each, and the sections a policy needs
- [`scripts/policy_scan.py`](scripts/policy_scan.py) — finds the services in manifests and source, checks the policy against them, flags contradicted claims and missing sections
- [`examples/habit-app.md`](examples/habit-app.md) — worked example: a habit app whose policy says it never shares data, beside a Meta pixel and an OpenAI call

## Quality bar

- **Every service named comes from the scan,** with its file and line or its package.
- **Every contradiction quotes the policy's sentence** and names the code that contradicts it.
- **Every gap has paste-ready text** that names the service, what it receives and why.
- **Dev-only tools aren't reported** as services that receive users' data.
- **What the code can't show is listed as questions,** not guessed.
- **The reply leads with what is untrue,** with no mention of scripts, files inside the skill or the skill itself.

## When to use this skill

- ✅ Before launch, an app-store submission or a customer's security questionnaire
- ✅ After adding an analytics, advertising or AI feature
- ✅ A policy copied from a template that nobody has checked against the product
- ✅ A customer or regulator asked "who do you share our data with?"

## When NOT to use this skill

- ❌ Writing a privacy policy for a product with no code yet: describe the data flows first
- ❌ A full data protection impact assessment for high-risk processing: that is a DPIA
- ❌ Terms of service, cookie banners and consent flows: this checks the policy's statements
- ❌ Contracts with vendors (data processing agreements): check the agreement itself

## Anti-patterns to avoid

- ❌ **Reviewing the policy's prose without opening the code.** The policy reads fine; it's the pixel that makes it untrue.
- ❌ **Reporting Segment from `devDependencies`.** Test and build tools never see a user.
- ❌ **"Consider updating your policy to mention third parties."** Write the paragraph.
- ❌ **Inventing vendors** "apps like this usually use". Only what the code shows.
- ❌ **Keeping "we never share your data"** with a softer adverb. With an ad pixel, it has to go.
- ❌ **Missing the AI call.** Text a user types into a feature that calls a model API leaves the service; say so and name the provider.
- ❌ **A disclaimer paragraph instead of the fix.**
