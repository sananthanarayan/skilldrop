---
name: context-graph
description: Map the decisions behind a codebase from its ADRs, RFCs and design records — each record's status and date, what supersedes or amends what, which records cite which, the files and folders each decision governs, and with git the commits that implemented it and the commits that changed each decision's code since it was made, and who made them — then answer "why is it like this?" from the record and check the record is still true. Finds supersessions only one side records, current decisions pointing at code that is gone, code that has drifted from its decision, two current decisions governing the same path, and references to records that don't exist. Use when the user asks "why do we use X", "which decisions govern this file or service", "is this ADR still current", "has the code drifted since we decided this", "are our ADRs out of date", "what was decided before I change this", wants a map of the architecture decisions, or is onboarding onto a codebase's history.
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
- **For this skill:** A rationale comes only from a record, quoted or cited by its id, and a record is only as true as the code: check the one that answers the question against the files it governs. When no record covers it, say "no recorded decision" and, at most, what the code shows, labelled as inferred. Never mention the script, the graph or any tool in the reply; say what the records and the code show.

1. **Find the records and build the graph with the script.** Read numbers, statuses and links from its output, not by eye. It finds records in the usual folders (`docs/adr`, `docs/decisions`, `docs/rfcs`, `architecture/decisions`, …) or the ones you name, and exits 2 when there are none.
   ```bash
   # Claude Code
   python3 "${CLAUDE_SKILL_DIR}/scripts/context_graph.py" --root .
   python3 "${CLAUDE_SKILL_DIR}/scripts/context_graph.py" --root . --why services/orders/consumer.py
   python3 "${CLAUDE_SKILL_DIR}/scripts/context_graph.py" --root . --record ADR-0004 --git
   # Other IDEs (from the skill folder)
   python3 scripts/context_graph.py --root <repo> --docs architecture/decisions --json -o graph.json --mermaid graph.mmd
   ```
   `--git` adds the commits whose messages mention each record. For each current decision that governs code, it also lists the commits that changed that code since the decision's date (or since the record was committed, when it has no date). It gives who made them, how many cite the record, and when the record itself was last edited. A path counts as governed when a record names it in backticks or links to it, and it exists. Without the script, do the same by hand and say the links were found by reading, not computed.

   **The script's findings are leads, not answers.** Confirm each one by reading the records and the code before you report it, and drop the ones that don't hold. Two records "governing the same path" often don't clash at all: say so only when their decisions actually conflict, and quote both.

2. **Answer "why" from the current record, and show the chain.** Say which decision governs the thing now, with its id, title, status and date, and the reason as the record states it. Then name what it replaced, if anything.
   - ✅ *"Order events moved from Kafka to SQS in ADR-0009 (accepted 2026-02-10): 'one fewer system to run, and the volume fits SQS'. ADR-0004 chose Kafka in 2025 and is still marked Accepted, so anyone reading it alone gets the wrong answer."*
   - ❌ *"You use Kafka for order events (ADR-0004), which gives you durability and ordering."* That reads the superseded record and adds a rationale that isn't in it.

3. **Trust the newest record only when the chain agrees.** A record superseded by another is history, even when its own Status line still says Accepted. The script lists each such one-sided supersession as a problem. Say which record a reader should rely on and why.

4. **Check the deciding record against the code.** Open the files it governs and check each thing the record requires (every "must", every named field, check, limit or setting), not only its headline. Confirm or contradict each with the code, quoting the line: ✅ *"`scheduler/jobs.py` line 18 still opens a database transaction per job, as ADR-0012 says."* Report drift as a finding with both sides: ✅ *"ADR-0015 promises 30 days of audit-log retention; `ops/logging.yaml` sets `retention_days: 14`."* When the record describes a phased change (a migration, a dual-write, a rollout), say which phase the code is in. While it's mid-rollout, the old decision still holds for the parts not yet moved: that is a missing cross-reference, not a contradiction.

   With git history, start with what changed since the decision: the commits to its code that don't cite it, newest first. Read what each one changed against the record's requirements. A commit is not drift by itself; a requirement the code no longer meets is. ✅ *"ADR-0009 (2026-02-10) requires one queue per tenant. Three commits since; `a1b2c3d` (Ben, 2026-05-03, 'Switch to shared queue') moved `orders/publish.py` to a single queue."* When the code changed a lot and the record was never touched, say so even when you find no contradiction. Name the people who made the changes: they are who to ask about what the record doesn't say.

5. **For "can I remove or change X?", search the code for every use of X,** not only the records: imports, client constructors, config keys, environment variables and container definitions. A use that no record covers is still a dependency: list it as "in use, no recorded decision", with its file. The records tell you why; only the code tells you everything that would break.

6. **Find the decisions that bear on it, not only the ones that name its path.** Read any record that amends, extends or narrows the governing one, and any that sets a rule for the same concern across the codebase (error handling, data access, logging, authentication), even when it names a different folder. A shared-library rule governs a change that creates a shared library. Before you call a related record unrelated, read it.

7. **Report what is no longer true, worst first.** Problems before warnings:
   - **Supersession recorded on one side only:** "ADR-0004 still says Accepted". Fix it by marking it "Superseded by ADR-0009".
   - **Code that no longer does what its current decision requires:** quote the requirement and the line, and name the commit that changed it when the history shows one.
   - **A current decision pointing at code that is gone:** the record names a folder or file that no longer exists. When the script suggests where it moved (a renamed sibling), or a README says so, report it as moved, not gone, and give the path to update. Only a path with no successor is gone; then the decision is dead, so deprecate it.
   - **A guide that still teaches a superseded decision:** an onboarding doc or a README that cites the old record, or describes its choice. Name the file and the line to change.
   - **Two current decisions governing the same path, neither superseding nor amending the other:** a possible conflict. Read both, quote the clash if there is one, and recommend which one supersedes or amends the other.
   - **A reference to a record that doesn't exist, a status that's missing or unrecognised, or a duplicate id.**

8. **Give each fix as the exact edit.** The line to change in which record, such as changing `## Status` to `Superseded by ADR-0009`, linked to that record's file, or the new record that's needed and what it must decide. Don't rewrite records nobody asked about.

9. **Say what the record can't tell.** Decisions made in chat or tickets and never written down, code that no record governs, and, without `--git`, whether anything was actually implemented or has changed since. When a question has no record, say so, and suggest writing one only if the decision is still live.

10. **Write the reply in this order, at the size asked for:**
   - the answer, in two or three sentences, with the governing record's id;
   - the chain or the problems, as a short list, each with its record id and the fix;
   - what the records don't cover;
   - "To confirm", only for inputs that are missing.

   Answer each question someone asked, in their order. A length they set is a limit: "two lines" is two lines, with the decision and the one thing they must not miss. When they say "keep it short" or "don't need an essay", give a few lines per question, and at most one line on record hygiene that doesn't change the answer. Give a table when they ask for a map, a list or something to paste; otherwise none. No closing offer or summary line.

**Non-interactive runs** (subagent, CI, headless): with no records found, emit `BLOCKED: no decision records found; name the folder that holds the ADRs or RFCs`. Exit 1 from the full check means problems were found. Report them; never edit the records yourself.

## Useful references in this skill

- [`reference.md`](reference.md): the record formats read (MADR, Nygard, RFC frontmatter), how status, supersession, amendment and governed paths are detected, every check and its fix, and the JSON shape
- [`scripts/context_graph.py`](scripts/context_graph.py): stdlib; builds the graph, checks it, answers `--why PATH` and `--record ID`; `--json`, `--mermaid`, `--git` (commits behind each record, and changes since each decision); exits 1 on problems and 2 on bad input
- [`examples/order-events.md`](examples/order-events.md): worked example, a repo whose Kafka ADR was superseded on one side only and whose newer ADR names a folder that was deleted

## Quality bar

- **The answer names the governing record by id, status and date**, and the rationale is quoted or closely paraphrased from that record. No reason is supplied that the record doesn't give.
- **A superseded record is never presented as current**, including one whose own Status line wasn't updated.
- **"No recorded decision" is said when it's true**, and any reading of the code is labelled as inferred.
- **Every problem names its record id and the exact fix.** Problems come before warnings.
- **Two current records on the same path are raised as a possible conflict**, not silently resolved by date.
- **The deciding record is checked against the code it governs, claim by claim,** with the line quoted, and drift is reported with both sides. A line number is given only when read from the file.
- **Every script finding in the reply has been confirmed by reading;** one that doesn't hold is dropped.
- **A removal or change question lists every use of the thing in the code,** recorded or not.
- **Related records are read before they're called unrelated:** amendments, and rules for the same concern elsewhere in the codebase.
- **A moved path is reported as moved, with its new location; only a path with no successor is "gone".**
- **Drift is a requirement the code no longer meets, with the record's words, the line, and the commit when the history shows one.** A count of commits is a reason to look, never a finding by itself.
- **A mid-rollout pair of records is a missing cross-reference, not a contradiction.**
- **The reply fits the size asked for (a stated limit is obeyed exactly), and never mentions a script, a graph or a tool.**
- **Statuses, links and governed paths come from the script's output**, or are marked as read by hand when it couldn't run.
- **No invented records, ids, dates, paths or commits.**

## When to use this skill

- ✅ "Why do we use X?" or "Why is this service built this way?" in a repo with ADRs or RFCs
- ✅ "Which decisions govern this file, folder or service before I change it?"
- ✅ "Are our ADRs still current?" or "Find the stale or contradictory decisions"
- ✅ "Has the code drifted from what we decided?" or "What changed in this service since the ADR, and who changed it?"
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
- ❌ **Passing on a script warning unread.** "Both govern the same path" is a prompt to read both, not a conflict.
- ❌ **Answering "can I remove it?" from the records alone.** The uses nobody recorded are the ones that break.
- ❌ **Taking the record's word for it.** A decision the code no longer follows is the most useful thing to find; read the files.
- ❌ **Calling it drift because the code changed.** Most commits since a decision implement or refine it. Only a requirement the code no longer meets is drift.
- ❌ **"Gone" for a folder that was renamed.** Look for where it went before telling someone the decision is dead.
- ❌ **Telling the reader how you found it.** "The script shows" or "the graph says" means nothing to them; say what the records and the code say.
