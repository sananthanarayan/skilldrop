# Reply-drafter judge — notes for the release gate

**Team:** Customer Support Tooling, Larkspur Telecom (fictional)
**Feature:** the reply drafter suggests an answer to each incoming support ticket; agents edit and send.

## What we did

- Sampled 80 drafted replies (R01–R80) from last week's tickets.
- Two LLM judges graded every reply pass/fail against one rubric: "Is this a good reply the agent
  could send as-is?" Each judge graded each reply twice (trial 1 and 2), same prompt, same settings.
  - `judge-a` is the larger model.
  - `judge-b` is the cheaper model, about a fifth of the cost per call.
- Our senior support lead, Maren Holt, graded R01–R40 by hand against the refund and contract
  policy. She did not see the judges' grades.
- `length` is the reply's word count.

All of it is in `judgements.csv`.

## What we want to decide

From next sprint, every prompt change to the reply drafter ships only if **`judge-b` passes at
least 85% of a fresh 80-reply sample**. `judge-b`, because it is cheaper; `judge-a` stays as a
spot check.

## Why we think it's fine

Tomás (ML engineer): "The two judges agree on 91% of replies, so the grading is reliable. Both
pass about 89% today, so we're comfortably over the 85% bar."
