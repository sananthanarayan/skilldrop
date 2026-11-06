# Worked example: a habit app's privacy policy

## Input

> *"We're launching TidyHabit next week. Can you check our privacy policy
> ([inputs/privacy-policy.md](inputs/privacy-policy.md)) against the app
> ([inputs/app/](inputs/app/))? We wrote it from a template in the spring."*

The app's `package.json` is kept here as `package.json.fixture`, so this repository's
dependency alerts don't read it; the scan ran with its real name.

## What the scan found

```text
| Service | Kind | Found in | Policy |
|---|---|---|---|
| Meta Pixel / Facebook SDK | advertising | src/layout.tsx:5, src/layout.tsx:6 | not disclosed |
| OpenAI | AI model API | package.json (openai) | not disclosed |
| PostHog | analytics and session replay | package.json (posthog-js) | not disclosed |
| Resend | email delivery | package.json (resend) | not disclosed |
| Sentry | error monitoring | package.json (@sentry/nextjs) | not disclosed |
| Stripe | payments | package.json (stripe), package.json (@stripe/stripe-js) | named |

FAIL Meta Pixel / Facebook SDK (advertising) is in the code (src/layout.tsx:5) but the policy names neither it nor its kind
FAIL OpenAI (AI model API) is in the code (package.json (openai)) but the policy names neither it nor its kind
FAIL PostHog (analytics and session replay) is in the code (package.json (posthog-js)) but the policy names neither it nor its kind
FAIL the policy contradicts the code: it says data isn't sold or shared with third parties (“We do not sell or share your personal information with third parties.”), but the code uses Meta Pixel / Facebook SDK
WARN Resend (email delivery) is in the code (package.json (resend)) but the policy names neither it nor its kind
WARN Sentry (error monitoring) is in the code (package.json (@sentry/nextjs)) but the policy names neither it nor its kind
WARN the policy doesn't cover cookies
WARN the policy doesn't cover transfers to other countries
WARN the policy doesn't cover children
```

The code confirms each finding: the pixel loads on every page from `src/layout.tsx`, with no
consent check; `src/coach.ts` sends the user's journal entry to OpenAI. Segment is in
`devDependencies` only and never reaches a user, so it isn't listed.

## Reply

**The policy isn't accurate yet, and one sentence in it is untrue.** It says *"We do not sell or
share your personal information with third parties"*, but every page loads the Meta pixel,
which sends visitors' page views and sign-ups to Meta for advertising. It also doesn't say that
journal entries go to OpenAI, or that PostHog records how people use the app.

**Services the policy doesn't mention**

- Meta Pixel (`src/layout.tsx`, line 5): page views, sign-ups, device and IP address, for advertising.
- OpenAI (`src/coach.ts`): the journal entry the user writes, to generate habit suggestions.
- PostHog (`package.json`): pages viewed, features used, device and approximate location.
- Sentry (`package.json`): error details, device and browser.
- Resend (`package.json`): email address and reminder emails.

**Replace, under "Sharing":**

> We don't sell your personal information. We share it with the service providers below, who
> process it for us, and with Meta for advertising, as described.
>
> - **Meta.** We use the Meta Pixel to measure our ads and show them to people who have visited
>   our site. It sends Meta the pages you view, whether you sign up, your device and browser, and
>   your IP address. You can opt out in our cookie settings.
> - **OpenAI.** When you ask for a habit suggestion, we send the journal entry you wrote to
>   OpenAI, which runs the AI model that writes the suggestion.
> - **PostHog** tells us which features people use, from the pages you view, your device and your
>   approximate location.
> - **Sentry** receives technical details when the app hits an error, so we can fix it.
> - **Resend** sends our reminder emails, and receives your email address to do it.
> - **Stripe** processes payments. We never see your full card number.

**Add these sections:** *Cookies* (the pixel and PostHog set them; say which and how to refuse),
*International transfers* (all six providers are in the US), and *Children* (a minimum age).

**Questions the code can't answer**

- Does your OpenAI plan use API data for training? (Check your organisation's data controls.)
- Does PostHog record sessions? It's on by default in some setups; check the project settings.
- Does anyone on the team export user data by hand, to a spreadsheet or a CRM?

**Worth a lawyer's hour:** if you'll keep the Meta pixel and have users in California, whether
retargeting counts as "sharing" there and needs a "Do Not Sell or Share" link.
