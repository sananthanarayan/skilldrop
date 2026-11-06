# Relevance judge bake-off — Wayfinder search (Kestrel Docs)

## What the judge is for

Our nightly retrieval eval asks an LLM judge whether each retrieved passage is `relevant` or
`irrelevant` to its query. From those labels we compute precision@5 per retriever build.

**The gate:** a retriever change ships only if its precision@5 is no more than 1.0 point below
the current production retriever's. So the judge's labels directly decide what ships.

## Volume and price

- Nightly run: ~20,000 query–passage judgments.
- Price per 1,000 judgments (from the vendor's October price sheet):

| Judge       | $ / 1k judgments |
|-------------|------------------|
| atlas-xl    | 4.80             |
| atlas-m     | 1.10             |
| atlas-nano  | 0.18             |

atlas-xl is the current production judge.

## This bake-off (`judgments.csv`)

- 300 query–passage pairs: 30 queries (`q01`–`q30`) x their top-10 retrieved passages.
- Each of the three judges labelled every pair once, same prompt, temperature 0.
- `passage_tokens` is the passage length. The index currently mixes legacy ~900-token chunks
  with newer short chunks (under ~400 tokens).
- `expert_label`: Priya Halvorsen (search lead) hand-labelled 60 pairs drawn uniformly at random
  from the 300. Blank means not expert-labelled. She was the only annotator.

## What's next

Q1 experiment: re-chunk the whole index to large chunks (~900 tokens) and compare the new
retriever against production through this same gate.
