---
name: context-graph
description: Map the decisions behind a codebase from its ADRs, RFCs and design records — each record's status and date, what supersedes or amends what, which records cite which, the files and folders each decision governs, and with git the commits that implemented it — then answer "why is it like this?" from the record and check the record is still true. Finds supersessions only one side records, current decisions pointing at code that is gone, two current decisions governing the same path, and references to records that don't exist. Use when the user asks "why do we use X", "which decisions govern this file or service", "is this ADR still current", "are our ADRs out of date", "what was decided before I change this", wants a map of the architecture decisions, or is onboarding onto a codebase's history.
---

# context-graph

Answers "why is it like this?" from what the team actually decided and wrote down, and says
plainly when nothing was written down. It reads every decision record (ADRs, RFCs, design
decisions), builds the graph between them and the code they govern, and checks that graph against
the repository as it is today. Writing a new or corrected record is `adr-generator`. Explaining how
the code works now, with no decision history, is `codebase-tour`. Recovering the architecture from
the code itself is `reverse-architecture`.

## How to respond

**Four rules come before the steps and outrank them:**

- **Answer what was asked, first.** Open with the answer, the decision or the artifact, in plain words. Scores, matrices, frameworks and tags come after it, and anything that doesn't change the answer is cut.
- **Use only what you were given.** Don't add facts, names, numbers, incidents, history, steps or sections the input doesn't contain. What you need and don't have is left out of the artifact and listed once at the end under "To confirm".
- **Deliver from what you have.** When the request gives you something to work on, state your assumptions in a line and produce the result. When it gives you nothing to work on, ask for it in one or two plain sentences and say what you will do once you have it.
- **Write for someone who has never heard of this skill.** No skill names, no paths or scripts from this folder, no internal terms, and nothing about how the run was set up. A next step is one plain sentence at the end that describes the work.
- **For this skill:** A rationale comes only from a record, quoted or cited by its id. When no record covers it, say "no recorded decision" and, at most, what the code shows, labelled as inferred, never as the team's reason.

1. **Find the records and build the graph with the script.** Read numbers, statuses and links from its output, not by eye. It finds records in the usual folders (`docs/adr`, `docs/decisions`, `docs/rfcs`, `architecture/decisions`, …) or the ones you name, and exits 2 when there are none.
   ```bash
   # Claude Code
   python3 "${CLAUDE_SKILL_DIR}/scripts/context_graph.py" --root .
   python3 "${CLAUDE_SKILL_DIR}/scripts/context_graph.py" --root . --why services/orders/consumer.py
   python3 "${CLAUDE_SKILL_DIR}/scripts/context_graph.py" --root . --record ADR-0004 --git
   # Other IDEs (from the skill folder)
   python3 scripts/context_graph.py --root <repo> --docs architecture/decisions --json -o graph.json --mermaid graph.mmd
   ```
   `--git` adds the commits whose messages mention each record. A path counts as governed when a record names it in backticks or links to it, and it exists. Without the script, do the same by hand and say the links were found by reading, not computed.

2. **Answer "why" from the current record, and show the chain.** Say which decision governs the thing now, with its id, title, status and date, and the reason as the record states it. Then name what it replaced, if anything.
   - ✅ *"Order events moved from Kafka to SQS in ADR-0009 (accepted 2026-02-10): 'one fewer system to run, and the volume fits SQS'. ADR-0004 chose Kafka in 2025 and is still marked Accepted, so anyone reading it alone gets the wrong answer."*
   - ❌ *"You use Kafka for order events (ADR-0004), which gives you durability and ordering."* That reads the superseded record and adds a rationale that isn't in it.

3. **Trust the newest record only when the chain agrees.** A record superseded by another is history, even when its own Status line still says Accepted. The script lists each such one-sided supersession as a problem. Say which record a reader should rely on and why.

4. **Report what is no longer true, worst first.** Problems before warnings:
   - **Supersession recorded on one side only:** "ADR-0004 still says Accepted". Fix it by marking it "Superseded by ADR-0009".
   - **A current decision pointing at code that is gone:** the record names a folder or file that no longer exists. Either the code moved, so update the paths, or the decision is dead, so deprecate it.
   - **Two current decisions governing the same path, neither superseding nor amending the other:** a possible conflict. Read both, quote the clash if there is one, and recommend which one supersedes or amends the other.
   - **A reference to a record that doesn't exist, a status that's missing or unrecognised, or a duplicate id.**

5. **Give each fix as the exact edit.** The line to change in which record, such as changing `## Status` to `Superseded by ADR-0009`, linked to that record's file, or the new record that's needed and what it must decide. Don't rewrite records nobody asked about.

6. **Say what the record can't tell.** Decisions made in chat or tickets and never written down, code that no record governs, and, without `--git`, whether anything was actually implemented. When a question has no record, say so, and suggest writing one only if the decision is still live.

7. **Write the reply in this order:**
   - the answer, in two or three sentences, with the governing record's id;
   - the chain or the problems, as a short list, each with its record id and the fix;
   - what the records don't cover;
   - "To confirm", only for inputs that are missing.

   Include the graph table or Mermaid diagram only when the user asked for a map.

**Non-interactive runs** (subagent, CI, headless): with no records found, emit `BLOCKED: no decision records found; name the folder that holds the ADRs or RFCs`. Exit 1 from the full check means problems were found. Report them; never edit the records yourself.

## Useful references in this skill

- [`reference.md`](reference.md): the record formats read (MADR, Nygard, RFC frontmatter), how status, supersession, amendment and governed paths are detected, every check and its fix, and the JSON shape
- [`scripts/context_graph.py`](scripts/context_graph.py): stdlib; builds the graph, checks it, answers `--why PATH` and `--record ID`; `--json`, `--mermaid`, `--git`; exits 1 on problems and 2 on bad input
- [`examples/order-events.md`](examples/order-events.md): worked example, a repo whose Kafka ADR was superseded on one side only and whose newer ADR names a folder that was deleted

## Quality bar

- **The answer names the governing record by id, status and date**, and the rationale is quoted or closely paraphrased from that record. No reason is supplied that the record doesn't give.
- **A superseded record is never presented as current**, including one whose own Status line wasn't updated.
- **"No recorded decision" is said when it's true**, and any reading of the code is labelled as inferred.
- **Every problem names its record id and the exact fix.** Problems come before warnings.
- **Two current records on the same path are raised as a possible conflict**, not silently resolved by date.
- **Statuses, links and governed paths come from the script's output**, or are marked as read by hand when it couldn't run.
- **No invented records, ids, dates, paths or commits.**

## When to use this skill

- ✅ "Why do we use X?" or "Why is this service built this way?" in a repo with ADRs or RFCs
- ✅ "Which decisions govern this file, folder or service before I change it?"
- ✅ "Are our ADRs still current?" or "Find the stale or contradictory decisions"
- ✅ A map of a codebase's architecture decisions for onboarding or a review

## When NOT to use this skill

- ❌ Writing a new ADR or fixing one: use `adr-generator`
- ❌ How the code works now, with no decision history: use `codebase-tour`
- ❌ Recovering the architecture from code with no records: use `reverse-architecture`
- ❌ A record of business or product decisions for stakeholders: use `decision-log`

## Anti-patterns to avoid

- ❌ **Reading one ADR and stopping.** The record that answers the question may have been superseded by a later one that never touched the first file.
- ❌ **Trusting a Status line over the chain.** "Accepted" on a record another record supersedes means someone forgot to update it, not that it is still in force.
- ❌ **Supplying the reason.** "Kafka gives you ordering" is general knowledge, not the team's decision. If the record doesn't say why, say it doesn't.
- ❌ **Resolving a conflict by date alone.** Two current records on the same path need a person to decide which wins; the newer one isn't automatically right.
- ❌ **Listing every record.** Answer the question; the full table is for a map that was asked for.
