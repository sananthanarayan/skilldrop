# Worked example — notifications epic → 5 stories

## Input (verbatim from the user)

> Epic: customers keep missing order updates. We want a notification system — order shipped, delivered, delayed. Should support email and SMS, let users pick which events they care about, and marketing wants to reuse it later for promos. Some customers are in the EU so there's consent stuff to think about.

## Output

# Story map: Order-update notifications

| # | Story | Slice | Depends on | Order |
|---|-------|-------|------------|-------|
| S1 | Customer gets an email when an order ships (walking skeleton) | Path | — | 1 |
| S2 | Customer gets emails for delivered and delayed events | Rules | S1 | 2 |
| S3 | Customer chooses which order events to receive | Path | S2 | 3 |
| S4 | Customer receives notifications by SMS | Interface | S3 | 4 |
| S5 | EU customer consent is captured before any notification | Rules | S1 | 2 (parallel with S2) |

## S1 — Customer gets an email when an order ships (walking skeleton)

**As a** customer with a placed order
**I want** an email the moment my order ships
**so that** I know it's on the way without checking the site

**Slice pattern:** Path
**Depends on:** —
[assumption] Email comes from the existing transactional-email provider; no new vendor selection in this epic.

### Acceptance criteria

- **AC1** Given a customer with a confirmed order and a valid email address, When the order's status changes to *shipped*, Then the customer receives a shipped email containing the order number and carrier tracking link within 5 minutes.
- **AC2** Given an order that changes to *shipped* twice due to a status replay, When the duplicate event arrives, Then no second email is sent.
- **AC3 (edge)** Given a customer whose email address hard-bounces, When a shipped event occurs, Then no retry storm occurs and the failure is visible in the service's logs/metrics.

### Out of scope for this story

- Delivered/delayed events → S2
- Channel or event preferences → S3, S4
- Consent gating → S5

## S2 — Customer gets emails for delivered and delayed events

**As a** customer with a shipped order
**I want** emails when my order is delivered or delayed
**so that** I'm not surprised by either outcome

**Slice pattern:** Rules (relaxes "shipped only" to all three events)
**Depends on:** S1

### Acceptance criteria

- **AC1** Given a shipped order, When its status changes to *delivered*, Then the customer receives a delivered email within 5 minutes.
- **AC2** Given a shipped order, When the carrier reports a delay, Then the customer receives a delayed email containing the new estimated date.
- **AC3 (edge)** Given an order that goes *delayed* then *delivered* within 10 minutes, When both events arrive, Then the customer receives both emails in event order, not interleaved.

### Out of scope for this story

- Customer choosing which of the three events to receive → S3

## S3 — Customer chooses which order events to receive

**As a** customer
**I want** to pick which order events notify me
**so that** I only get the updates I care about

**Slice pattern:** Path
**Depends on:** S2
[assumption] Default for existing customers is all order events ON — opt-out, not opt-in (overridden by S5 for EU customers).

### Acceptance criteria

- **AC1** Given a logged-in customer on notification settings, When they turn *delayed* off and save, Then subsequent delay events produce no email and the setting survives logout/login.
- **AC2** Given a customer with all events off, When any order event occurs, Then no notification of any kind is sent.
- **AC3 (edge)** Given a settings save that fails server-side, When the customer saves, Then the UI shows the failure and the previous settings remain in effect — no silent partial save.

### Out of scope for this story

- Per-channel preferences (email vs SMS separately) → S4

## S4 — Customer receives notifications by SMS

**As a** customer who prefers texts
**I want** order notifications by SMS
**so that** I see them without opening email

**Slice pattern:** Interface (adds a channel to existing behavior)
**Depends on:** S3
[assumption] One SMS provider, chosen by the team's existing vendor list; international SMS limited to countries the store ships to.

### Acceptance criteria

- **AC1** Given a customer with a verified phone number and SMS enabled, When a subscribed order event occurs, Then they receive an SMS within 5 minutes containing order number and a short status line.
- **AC2** Given a customer with both channels enabled, When an event occurs, Then they receive both email and SMS for that event.
- **AC3 (edge)** Given an unverified phone number, When the customer enables SMS, Then sending is blocked until verification completes and the UI says so.

### Out of scope for this story

- Quiet hours / time-zone batching → not covered, listed in epic out-of-scope

## S5 — EU customer consent is captured before any notification

**As an** EU customer
**I want** to be asked for consent before receiving notifications
**so that** my communication preferences are lawful and mine

**Slice pattern:** Rules (tightens the default-on rule for one jurisdiction)
**Depends on:** S1

### Acceptance criteria

- **AC1** Given a customer whose account country is in the EU and who has not consented, When any order event occurs, Then no notification is sent on any channel.
- **AC2** Given an EU customer presented the consent prompt, When they accept, Then the consent decision, timestamp, and scope are stored and notifications begin from the next event.
- **AC3 (edge)** Given an EU customer who previously consented, When they withdraw consent, Then notifications stop from the next event and the withdrawal is stored with a timestamp.

### Out of scope for this story

- Legal review of the consent copy — flagged for the compliance team, not an engineering AC.

## Out of scope / not covered by any story

- **Marketing/promo notifications** — the epic mentions marketing reuse "later"; nothing here builds promo sending. The event-driven design keeps it possible.
- **Push notifications** — only email and SMS were requested.
- **Quiet hours / batching** — not requested; revisit if SMS complaint volume appears.
