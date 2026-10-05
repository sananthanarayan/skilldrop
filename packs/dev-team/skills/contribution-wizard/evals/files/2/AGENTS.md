# Instructions for agents working in this repo

Read `CONTRIBUTING.md` first. The rules below were added after it and win where the two differ.

1. **A skill never calls, starts or hands off to another skill.** Each folder has to work when it is the only one installed. If a second skill is the natural follow-up, say so to the user in the final line of the output and let them run it.
2. **Five test cases minimum, not three.** At least one case must cover missing input: the user leaves out something listed under `inputs`, and the expected behaviour is that the skill says what is missing and does not guess.
3. **No customer or carrier names from real accounts** in instructions or tests. Use made-up ones.
4. **Money rules are written as numbers.** If a skill applies a threshold or tolerance, the exact figure goes in `INSTRUCTIONS.md`. "A reasonable tolerance" is not acceptable.
5. Do not edit `OWNERS.md`. If no listed team fits, ask in the pull request.
