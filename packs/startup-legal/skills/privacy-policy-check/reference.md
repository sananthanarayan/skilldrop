# Disclosure wording, by kind of service

Each block: what the service usually receives, and a paragraph to adapt. Replace the bracketed
parts with what this app does; name the actual provider the code uses. Keep the policy's own
voice ("we", "you").

## Advertising pixels and SDKs (Meta, Google Ads, TikTok, LinkedIn, X)

Receives: page views and events (sign-up, purchase), device and browser data, IP address, and
the cookie or advertising ID that links them to the person's account on that platform.

> We use [Meta Pixel] to measure our advertising and show our ads to people who have visited our
> site. It sends [Meta] information about your visit, such as the pages you view, the actions you
> take (like signing up), your device and browser, and your IP address. [Meta] may combine this
> with information it already holds about you. You can opt out in [our cookie settings / your
> Facebook ad preferences].

A pixel used for retargeting can count as "sharing" or "selling" under some laws (California's
CCPA among them). A policy that says "we do not sell or share your personal information" must
change, not soften.

## Analytics and session replay (Google Analytics, PostHog, Mixpanel, Amplitude, Hotjar, FullStory, Clarity)

Receives: pages and screens viewed, clicks and events, device and browser data, approximate
location from IP address; session replay also records what is on screen and mouse movement.

> We use [PostHog] to understand how people use [the app], so we can improve it. It receives the
> pages you view, the features you use, your device and browser type, and your approximate
> location from your IP address. [We record sessions to see where people get stuck; we mask
> text you type and do not record payment fields.]

## AI model APIs (OpenAI, Anthropic, Google Gemini, Mistral, Cohere)

Receives: whatever the feature sends: often the text the user typed, files they uploaded, or
their conversation history.

> When you use [the habit suggestions feature], we send [the journal entry you write] to
> [OpenAI], which provides the AI model that generates the suggestion. [OpenAI] processes it to
> return a response [and, under our agreement with it, does not use it to train its models]. Do
> not include information in [journal entries] that you don't want processed this way.

Check the provider's data-use terms for the plan in use before claiming it doesn't train on
the data; list it as a question if unknown.

## Error monitoring (Sentry, Bugsnag, Datadog, Crashlytics)

> We use [Sentry] to find and fix errors. When something goes wrong, it receives technical
> details about the error, your device and browser, and [your user ID], so we can investigate.

## Payments (Stripe, PayPal, Razorpay, Paddle)

> Payments are processed by [Stripe]. When you pay, you give your card details directly to
> [Stripe]; we never see or store your full card number. [Stripe] shares with us the last four
> digits, card type, and billing country to show in your account.

## Sign-in and hosting (Auth0, Clerk, Firebase, Supabase)

> We use [Supabase] to host our database and manage sign-in. It stores your account details and
> the content you create in [the app], on our behalf.

## Email, SMS and support chat (Resend, SendGrid, Postmark, Mailchimp, Twilio, Intercom, Crisp)

> We use [Resend] to send you account and reminder emails, [Mailchimp] for our newsletter if you
> sign up, and [Intercom] to answer your support messages. Each receives your email address and
> the content of the messages.

## Maps, search, media and push (Google Maps, Mapbox, Algolia, Cloudinary, OneSignal)

> [Mapbox] receives your approximate location when you use the map. [Cloudinary] stores the
> photos you upload. [OneSignal] receives a device token to send you notifications.

## Sections every policy needs

- **Who we are and how to contact us:** company name, address, a privacy contact email.
- **What we collect and why:** each kind of data, its purpose and, in the EU and UK, the legal
  basis (contract, consent, legitimate interests).
- **Who receives it:** the services above, by name or kind.
- **How long we keep it:** a period for each kind, or the rule ("until you delete your account,
  then 30 days").
- **Your rights:** access, correction, deletion, objection, portability, and how to use them;
  how to complain to the regulator.
- **Cookies:** what the site sets and how to refuse them, when it sets any beyond the strictly
  necessary.
- **International transfers:** when a provider is in another country (most are in the US), and
  the safeguard relied on (standard contractual clauses, the EU–US Data Privacy Framework).
- **Children:** the minimum age for the service, and that it doesn't knowingly collect
  children's data (or what it does if it does).
- **Changes:** how users learn of an update, and the date of this version.

## When a lawyer earns the fee

Name these only when they apply:
- children under 13 (16 in parts of the EU) use the product;
- health, financial, biometric or precise location data;
- the app sells data, or shares it with ad networks, to users in California or other states
  with opt-out laws;
- the founder targets a country whose rules they have never dealt with, at meaningful scale.
