# Grant application screening: planned Claude workflow

Merrow Arts Foundation (invented). Each application arrives as a PDF, is converted to plain text,
then goes through three stages.

## Stage 1: extract (small model)

- Input: extraction instructions (about 3,000 characters) plus the full application text.
  Applications average about 18,000 characters; the largest we have seen was about 60,000.
- Output: a JSON record of the applicant, project, amount and dates, about 1,200 characters.
- max_tokens is currently set to 4,096.

## Stage 2: score (large model, agent loop)

- System prompt: scoring instructions (about 4,000 characters) plus the scoring rubric
  (about 8,000 characters).
- First user message: the stage 1 JSON record.
- The model calls the check_eligibility tool about 4 times per application. Each tool result is
  about 2,000 characters of JSON. Each tool-call turn produces about 150 output tokens.
- The full conversation history is kept and re-sent on every turn.
- The final turn returns a score and justification of about 600 characters.

## Stage 3: summary (small model)

- Input: summary instructions (about 1,000 characters), the stage 2 score and justification, and
  the full application text again.
- Output: a 300-word summary for the grants panel.
- max_tokens is currently set to 4,096.

## Volume

About 1,200 applications per funding round, three rounds a year, so about 4,800 applications a
year.

## Planning prices (from finance, per million tokens)

| Model | Input | Output |
|-------|-------|--------|
| small | $0.80 | $4.00  |
| large | $3.00 | $15.00 |

Finance has approved a cap of $400 a year for this workflow.
