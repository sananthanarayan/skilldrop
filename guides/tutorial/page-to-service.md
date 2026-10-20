---
title: From an unreadable page to a service people can use
summary: Rewrite a council permit page from what residents need, write every word on the application form, then blueprint the service behind it and find why two thirds of the calls are "where is my permit", with the experience-design pack.
kind: tutorial
---

# From an unreadable page to a service people can use

In about twenty minutes you'll take one council service through three layers of its
experience. You'll rewrite the page residents read, write every button, error and status
message on the form they fill in, and then map the service behind both. That last step
explains the calls a better page alone wouldn't stop. Each layer finds something the one
before it couldn't.

Everything quoted below is from a real run on Claude Sonnet 5 with the two files on this
page, with the three requests below sent as one message. The page text is the
`content-design` skill's own example; the team lead's notes were written for this tutorial.

## Install the pack

```bash
npx skilldrop-cli install --pack experience-design
```

This adds `information-architecture`, `content-design`, `ux-writing`, `design-system-spec`
and `service-blueprint`, plus `core`. This tutorial uses three of them.

## Gather the page and what the team knows

Save the page as it reads today in `before.md`:

```text
Residents' Parking Scheme Information

Northwind Council operates a Controlled Parking Zone (CPZ) scheme in designated areas of the borough in order to prioritise the availability of on-street parking for residents and their visitors. Applications for a resident parking permit may be submitted by any individual whose principal residence is located within a CPZ, subject to the provision of satisfactory documentary evidence of both residency and vehicle ownership or keepership. Permits are issued for a period of twelve months and the applicable charge is determined with reference to the CO2 emissions band of the vehicle in question. Applicants should be aware that the processing of applications may take up to ten working days from receipt of all required documentation. In the event that an applicant does not possess the requisite documentation, the application will be held in abeyance until such time as it is provided.
```

Then write down how the service works, as the permits team lead would tell it. Save it as
`service-notes.md`:

```text
- Residents apply on the website: four screens. 1) Check your address is in a zone
  (postcode lookup). 2) Your vehicle (registration; we look up the CO2 band from DVLA).
  3) Upload proof of address and the V5C logbook. 4) Pay by card.
- Uploads go to a shared inbox. Two permit officers check documents by hand, oldest first.
  Average 6 working days before anyone opens an application; 9 in September.
- If a document is wrong, the officer emails the resident from their own mailbox. About 1 in
  4 applications get this email. The website still shows "Submitted" while it waits.
- Approved permits are typed into Parkwise. Wardens' handhelds sync overnight.
- Residents get no message when the permit goes live. Some get a ticket the next morning.
- ~1,100 calls a month to the permits line; the lead thinks two thirds are "where is my permit".
- Errors on the form today: "Invalid input", "Upload failed", "Postcode not recognised",
  "Payment declined".
```

## Rewrite the page from what residents need

> Rewrite the permit page in before.md from what residents need, with a readability check
> on before and after. Residents are all ages, lots on phones; our top calls are "how long
> does it take" and "what documents do I need". Proof of address is a council tax bill; for
> the car it's the V5C logbook. How the service works is in service-notes.md.

`content-design` writes the user needs first, puts the questions in the order residents ask
them, and then drafts the page. The readability script measures both versions:

| | Before | After |
|---|---|---|
| Avg sentence (words) | 24.0 | 10.1 |
| Long words (3+ syllables) | 24.3% | 5.4% |
| Estimated grade (heuristic) | 15.1 | 4.1 |
| Sentences over limit (25 / 20 words) | 4 | 0 |

The new page is longer: 223 words against 144. It keeps every fact and adds a section the
old page never had, because the notes show where the calls come from:

> Once your permit is approved, wait until the next day before you rely on it. It takes until
> the following day for parking wardens' handheld devices to show your new permit.

## Write every word on the form

> Write the interface text for the four application screens: buttons, labels, errors and
> the status messages a resident sees after submitting. Our voice is plain and friendly, no
> exclamation marks.

`ux-writing` returns a string table: an ID, a character budget, a recommended line and a
variant for each slot. Each of the four vague errors is replaced with one that names the
field and the fix:

| Today | Now |
|---|---|
| Invalid input | That's not a registration number we recognise. Check it for typos, like 0 for O. |
| Upload failed | {filename} didn't upload. Check your connection and try again. |

Then it writes status messages the service doesn't send yet. "Action needed" replaces an
officer's email from a personal mailbox. "Approved" says the permit is active from tomorrow.

Read the lines marked `[inferred]` before you ship them. The payment-failure message says
"You haven't been charged". That's only true if your payment provider guarantees it, so
check with whoever runs payments. The skill marked it because nobody had said so.

## Map the service behind the form

> Blueprint the service from a resident applying to parking legally with the permit, with
> the fail points and the fixes ranked.

`service-blueprint` lays out seven steps across what the resident does, what they see, and
what happens behind the line of visibility. The worst fail points are backstage. Documents
land in a shared inbox that nobody owns. The status never changes during review. A rejected
document is chased from someone's personal mailbox. And the handhelds sync overnight only.
It ranks three fixes:

1. A resident checking their application sees a real status that changes as officers work
   it, instead of a frozen "Submitted".
2. A resident is told automatically, on a channel they'll see, when a document is rejected
   or a permit is approved.
3. A resident is told plainly to wait a day before relying on a new permit, until the
   handhelds can sync the same day.

The first two are why "where is my permit" is two thirds of the calls. A better page
couldn't fix them, and a better form couldn't either.

## What you have now

A page residents can read on a phone, a string table a developer can paste in, and a
blueprint that shows the digital team and the permits team which fix comes first. Each file
ends with its open questions, such as prices by CO2 band and upload size limits. Those are
left as questions, not filled in with guesses.

Next: [Use the experience-design pack](../how-to/packs/use-the-experience-design-pack.md) for
`information-architecture` and `design-system-spec`, or
[Every skill in the experience-design pack](../reference/packs/pack-experience-design.md).
