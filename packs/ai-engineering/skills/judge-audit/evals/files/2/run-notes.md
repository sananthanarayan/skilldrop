# Onboarding email prompt — v1 vs v2

**Team:** Growth, Quillmark (fictional)

- 50 sign-up profiles (E01–E50). For each, prompt v1 and prompt v2 each wrote a welcome email.
- One LLM grader (`grader-1`) saw both emails for a profile and picked the better one, or `tie`.
  It ran twice per profile (trial 1 and 2). Which email was shown as A was randomised on every run.
- `winner` is the prompt whose email the grader picked. `position` is where that email was shown
  (A first, B second). `length` is the picked email's word count; `other_length` is the other's.

Data: `pairwise.csv`.

## Result so far

v2 won 53 comparisons, v1 won 43, 4 ties. Plan: switch production to v2 this sprint and use the
same grader setup for every future prompt change.
