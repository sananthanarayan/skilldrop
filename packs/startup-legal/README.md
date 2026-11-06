# Startup legal

Legal groundwork for a startup that can't yet pay a lawyer for everything: an agreement checked before you sign it (blanks, broken cross-references, mismatched amounts, the renewal date, and the clauses that hurt a small company, with wording to ask for), and your cap table modelled through SAFEs, notes and a priced round. Each says what is worth a lawyer's hour.

`/plugin install startup-legal@skilldrop` · generated from [`main`](https://github.com/sananthanarayan/skilldrop) — do not edit.

## Start here: Check an agreement before you sign it

Paste this into Claude Code:

```text
We're the customer in this SaaS agreement (agreement.docx), and the first year ends on 1 July 2027. Review it before I sign: what's broken, what should I push back on, and when do we have to give notice if we don't want it to renew?
```

- **Before you start:** The agreement you've been sent, as a Word, Markdown or text file
- **Before you start:** Python 3 on the machine, which the checks run on
- **How to tell it worked:** contract-check opens with a verdict and the three things that matter most, lists each mechanical fault with its clause number (blanks, references to clauses or exhibits that don't exist, amounts whose words and figures disagree), gives wording to ask for on each clause that hurts you, and gives the renewal notice deadline as a date.
- **If nothing happens:** If contract-check does not activate, ask for it by name ("use contract-check"). If your agreement is a PDF, save it as Word or text first.

## Loops

- `ship-a-draft`

## Skills

- `brief-intake`
- `cap-table`
- `context-graph`
- `contract-check`
- `council-review`
- `doc-critique`
- `output-hygiene`

More: https://sananthanarayan.github.io/skilldrop/packs/startup-legal/
