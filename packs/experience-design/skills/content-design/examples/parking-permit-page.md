# Worked example — a council parking permit page, rewritten from user needs

## Input given to the skill

> Can you redo our resident parking permit page? It's the current text below and we get a lot of
> calls asking "how long does it take" and "what documents do I need". Our usual proof of address is
> a council tax bill and for the car it's the V5C logbook. Readers are residents, all ages, lots of
> them reading on a phone.

Current page (`before.md`):

> Residents' Parking Scheme Information
>
> Northwind Council operates a Controlled Parking Zone (CPZ) scheme in designated areas of the borough in order to prioritise the availability of on-street parking for residents and their visitors. Applications for a resident parking permit may be submitted by any individual whose principal residence is located within a CPZ, subject to the provision of satisfactory documentary evidence of both residency and vehicle ownership or keepership. Permits are issued for a period of twelve months and the applicable charge is determined with reference to the CO2 emissions band of the vehicle in question. Applicants should be aware that the processing of applications may take up to ten working days from receipt of all required documentation. In the event that an applicant does not possess the requisite documentation, the application will be held in abeyance until such time as it is provided.

## Output

# Content spec: Apply for a resident parking permit

**Reader:** a resident in a controlled parking zone who wants to park near home, often on a phone · **Target level:** plain English for a general audience
**Channel:** web page · **Assumptions to confirm first:** the page is only for resident permits, and visitor permits have their own page.

### User needs

| # | As a… | I need… | So that… | Evidence |
|---|---|---|---|---|
| 1 | resident in a parking zone | to know if I can get a permit | I don't apply for something I can't have | [assumption] |
| 2 | resident applying | to know which documents to have ready | I can apply in one go | [support calls] "what documents do I need" |
| 3 | resident applying | to know how long it takes | I can plan where to park until it arrives | [support calls] "how long does it take" |
| 4 | resident applying | to know what it costs | I can budget for it | [assumption] |

### Questions the page must answer (priority order)

1. Can I get one? — it decides whether the rest of the page matters
2. What do I need? — the top call reason, and it's what stops an application
3. How much is it? — asked before people start
4. How long does it take? — the other top call reason, but only after they've decided to apply

### Structure

| Order | Heading (reader's words) | Answers | Format |
|---|---|---|---|
| 1 | Apply for a resident parking permit — first two sentences say who can apply | Q1 | paragraph |
| 2 | What you need | Q2 | list |
| 3 | How much it costs | Q3 | paragraph |
| 4 | How long it takes | Q4 | paragraph |

### Draft (`after.md`)

> # Apply for a resident parking permit
>
> You can apply if you live in a controlled parking zone. A permit gives you priority for parking on the street in your zone.
>
> ## What you need
>
> - proof you live at the address, like a council tax bill
> - proof you own or keep the car, like the V5C logbook
>
> ## How much it costs
>
> The price depends on your car's CO2 emissions band. A permit lasts 12 months.
>
> ## How long it takes
>
> It can take up to 10 working days. We start counting when we have all your documents. If something is missing, we hold your application until you send it.

### Readability (script output, before → after)

Run: `python3 scripts/readability.py before.md` and `python3 scripts/readability.py after.md --max-sentence 20`.

```
before.md
Words: 144  Sentences: 6  Avg sentence: 24.0 words
Long words (3+ syllables): 24.3%
Estimated Flesch-Kincaid grade: 15.1 (heuristic syllables; compare before/after, don't quote as exact)
Sentences over 25 words: 4

after.md
Words: 105  Sentences: 13  Avg sentence: 8.1 words
Long words (3+ syllables): 5.7%
Estimated Flesch-Kincaid grade: 2.7 (heuristic syllables; compare before/after, don't quote as exact)
Sentences over 20 words: none
```

(The before count includes the title line as a sentence. The four flagged sentences are the four long ones in the source.)

### Cut list

| What was cut | Why | Where it went |
|---|---|---|
| "Northwind Council operates a Controlled Parking Zone (CPZ) scheme…" | Organisational message. What a zone does for the reader is kept in one sentence. | Shortened into the opening paragraph |
| "…and their visitors" | Visitor permits are a different task | Visitor permits page (confirm it exists) |
| "subject to the provision of satisfactory documentary evidence" | Replaced by the concrete documents | "What you need" list |
| The acronym "CPZ" | Readers don't use it; it appeared twice and was never needed | Removed |

Kept on purpose: "own or keep the car" keeps "keepership" from the source, because a keeper who isn't the owner can still apply. "Up to 10 working days" keeps the source's limit, not a promise of a shorter time.

### Open questions

- What are the prices per emissions band? The page should show them, or link to them.
- Is there an "Apply now" link, and does it need a form? If so, its strings go to `ux-writing`.
- Which documents count besides a council tax bill and a V5C? List them if there are others.
