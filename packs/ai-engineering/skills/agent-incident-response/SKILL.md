---
name: agent-incident-response
description: Plan the first hour after something went wrong with an AI coding agent or its tooling — a leaked or stolen API key, a destructive command (a dropped table, a force-push), a runaway bill, a malicious MCP server or skill, an agent prompt-injected into sending data out. It answers the person's actual question first, reads their logs for what they didn't mention, splits a bill from the usage export, gives the exact recovery for what was destroyed, revokes at the provider before cleanup when the evidence says the credential is in someone else's hands, and lays out the first 15 minutes, the next hour and who to tell. Use when the user says "I leaked my API key", "the agent committed a secret", "the agent deleted / force-pushed / dropped something", "is the table gone for good", "huge bill overnight", "we installed a malicious MCP server", "our agent platform was breached", or "what do I do now".
---

# agent-incident-response

The first hour after an agent incident, as actions the person takes now, in the order that
stops the damage. A capable agent writes a tidy incident process and misses three things: the
answer to the question the person asked, the line in their own log that changes the plan (a
second caller on the key, a second table dropped, someone else's commits overwritten), and the
exact command that gets the lost thing back. This skill puts those first.

## How to respond

**Four rules come before the steps and outrank them:**

- **Answer what was asked, first.** Open with the answer, the decision or the artifact, in plain words. Scores, matrices, frameworks and tags come after it, and anything that doesn't change the answer is cut.
- **Use only what you were given.** Don't add facts, names, numbers, incidents, history, steps or sections the input doesn't contain. What you need and don't have is left out of the artifact and listed once at the end under "To confirm".
- **Deliver from what you have.** When the request gives you something to work on, state your assumptions in a line and produce the result. When it gives you nothing to work on, ask for it in one or two plain sentences and say what you will do once you have it.
- **Write for someone who has never heard of this skill.** No skill names, no paths or scripts from this folder, no internal terms, and nothing about how the run was set up. A next step is one plain sentence at the end that describes the work.
- **For this skill:** The first line answers the person's question with the fact from their files that decides it. ✅ *"No, max_turns alone won't fix this: $840.00 of the $1,910.00 came from a second caller on the same key, not the loop."* ✅ *"Very likely not gone: the instance keeps three days of point-in-time restore. Restore it to a new instance today."* ❌ *"This is a serious incident. Here is a structured response plan."*

1. **Read every file given, line by line, before planning.** The person describes the part they
   noticed; the plan turns on the part they didn't: a second table dropped or a constraint
   removed by `CASCADE`; a force-push line `+ <old>...<new>` over another author's commits;
   credentials printed in a log they pasted into a channel; a run log whose last line shows the
   loop still going (the process is live); usage the job's config doesn't produce; a config
   comment like "shared with the billing bot"; a retention period or the owner team.

2. **Compute numbers; never estimate them.** Split a bill from the usage export with the
   script, over the incident window only (drop the normal nights before it, or the split is
   off by their few dollars):

   ```bash
   # Claude Code
   python3 "${CLAUDE_SKILL_DIR}/scripts/usage_split.py" <usage.csv> --since <first incident hour> --expect model=<job's model> --expect user_agent=<job's client>
   # Other IDEs (from the skill folder)
   python3 scripts/usage_split.py <usage.csv> --since <first incident hour> --expect model=<job's model> --expect user_agent=<job's client>
   ```

   It sums cost exactly per key, model and client, lists each group's hours, and marks what
   the job doesn't explain. Quote its figures to the cent and the hours as the export
   writes them, in UTC. ❌ *"About $1,075 is the loop"* when the window sum is $1,070.40.
   ❌ *"Started around 20:00Z"* when the first row says 22:00Z.

3. **Name the kind of incident, with the fact that decides it, and size the response to it.**
   - **Cost only:** every dollar is explained by the person's own job (its model, its client,
     its hours) and nothing shows the key went anywhere else. Stop the job, fix the cause, set a
     spend limit. No security process: ❌ evidence chains, legal flags and a hardening list
     for a loop on a 429.
   - **Possible compromise:** spend, calls or logins the known job doesn't explain, or the key
     sitting where others can read it (committed in plaintext, printed in a pasted log, stored on
     a breached platform). Revoke first, before any config change. ✅ *"A curl client
     calling the largest model isn't your job: treat the key as in someone else's hands."*
   - **Destructive:** data, commits or infrastructure removed. Recovery comes first, because
     restore windows close; stop all writes to what was hit.
   - **Data out:** secrets, code or personal data sent somewhere. Not over at revocation; over
     when the path out is closed and what could have left is listed.

4. **Revoke at the provider before any cleanup, when a credential is exposed.** Deleting the
   commit, the chat message or the key on an agent platform revokes nothing. Revoke **every
   credential the thing held** (the session's env, the server's env block, the pasted log), not
   only the one noticed. When another service shares the key, give each service its own new
   key, swap it in, revoke the old one inside the hour, and warn that service's owners first. A
   key in git history stays exposed after it moves to a secret store. Where to revoke, per
   provider: [`reference.md`](reference.md); name the console area in words, never a URL.

5. **Stop what's still acting, in the same minute.** Kill the live process on the host the
   files name, pause the schedule, keep the agent session closed and don't resume it in an
   auto-accept or permission-bypass mode. Confirm from the log that nothing ran after the
   interrupt. **Save before cleaning up:** the transcript, run log, usage export and
   config as they are (keys by prefix and last four only), then clean up; remove a pasted log
   from a channel only after keeping an unredacted copy.

6. **Give the exact recovery for what was destroyed, with the SHAs, names and times from the
   input.**
   - **Force-push:** the overwritten tip is the `<old>` in the push line. It survives in the
     pushing clone's reflog for the remote-tracking branch, in any clone that fetched before
     the push, and on the host's pull-request refs. Tell the overwritten commits' author not to
     pull, reset or run `gc`/`prune` until it's back.

     ```bash
     git reflog show origin/<branch>               # in the clone that pushed: find <old-sha>
     git branch recovery/<branch> <old-sha>        # pin it before anything is pruned
     git push origin recovery/<branch>             # put it back on the remote, then merge
     ```

     Restore the branch itself only once the commits' author agrees; the squashed local commit
     still holds the pusher's work.
   - **Dropped table:** restore point-in-time to a **new instance**, just before the drop
     time in the log, then copy the rows back into the live database; never restore over it.
     State the deadline (drop time plus the retention period in the infrastructure file), that
     rows written after the restore point are not in the copy, and which constraints `CASCADE`
     removed. Name every table the log shows dropped. More in [`reference.md`](reference.md).

7. **Scope by what the credential could reach, not what is known to be touched.** Every
   project, model, repo or account its scopes cover, from first exposure to revocation. When a
   key may sit in a repo or logs, find every copy with the masked finder:

   ```bash
   # Claude Code
   python3 "${CLAUDE_SKILL_DIR}/scripts/find_secret_exposure.py" --prefix <first 10+ chars> --suffix <last 4> --repo <path> --log <log.txt>
   # Other IDEs (from the skill folder)
   python3 scripts/find_secret_exposure.py --prefix <first 10+ chars> --suffix <last 4> --repo <path> --log <log.txt>
   ```

8. **Say who to tell, and by when,** using the names, teams and channels in the files: the
   owner of what was hit, the author of overwritten work, the owners of services sharing the key,
   the security contact when it's a possible compromise, the provider and finance for spend
   nobody authorised. Personal data in reach: the privacy lead the same day; flag the possible
   legal duty without deciding it.

**Never invent environment facts.** Only what the files show, labelled by where it came from:
✅ *"The session ran in auto-accept mode (session header)."* ❌ *"The sandbox blocks internal
hosts"* when nothing says so. ❌ Calling a value live, a backup present or a commit discarded
unless a file shows it. Console and network steps are actions for the person, not things done.

**Reply shape** (chat length; no tables unless asked):
- The answer line, then one line: the kind of incident and the deciding fact.
- **Next 15 minutes:** numbered actions, each with an owner (you, or the team or person the
  files name) and how to tell it's done: revoke, stop, pin the lost commit, start the restore.
- **Next hour:** finish the recovery, scope check, spend limit, and the cause from the log (a retry
  with no backoff, no turn cap, a session in bypass mode) with one control. ❌ A hardening list.
- **Tell:** who, by when, in a line each.
- **To confirm:** only what's unknown and would change an action. Omit when empty.

**Non-interactive runs** (subagent, CI, headless): an unnamed provider, unknown scopes and an
unknown exposure time become `[assumption]` at their worst plausible value (widest scope,
earliest time), listed at the top. With no incident described at all, emit
`BLOCKED: need what happened: which credential, agent or tool, and when it was noticed`, then
say in plain words what the plan will cover once it is given.

## Useful references in this skill

- [`reference.md`](reference.md) — where to revoke per provider, what each leak location keeps, recovery after destructive commands, evidence, notification table, controls
- [`scripts/usage_split.py`](scripts/usage_split.py) — splits a usage export by key, model and client, exact to the cent, marking traffic the job doesn't explain (stdlib, read-only)
- [`scripts/find_secret_exposure.py`](scripts/find_secret_exposure.py) — finds a key in git history and logs, masked (stdlib, runs `git`, read-only)
- [`examples/injected-issue-comment.md`](examples/injected-issue-comment.md) — worked example: a triage agent prompt-injected into posting its tokens

## Quality bar

- **The first line answers the question asked;** the second names the kind of incident and its evidence.
- **Every figure and time matches the files,** sums computed, times in UTC as written.
- **What the person didn't mention is found:** the second table, caller or repo, the live process.
- **Recovery is exact:** SHAs, the restore point, the deadline, the caveats, an owner on each action.
- **An exposed credential is revoked before cleanup,** every one the thing held, with sharing services warned.
- **Nothing invented:** no environment facts, URLs, figures or attacker actions not in the files.

## When to use this skill

- ✅ An API key or token was pasted in a commit, a prompt, a log or a chat
- ✅ An agent dropped data, force-pushed, deleted files or changed infrastructure
- ✅ A large or unexplained bill on a model provider or cloud account
- ✅ An agent platform holding stored keys announced a breach
- ✅ A malicious or impostor MCP server, skill, plugin or hook was installed
- ✅ An agent was prompt-injected and may have sent data out

## When NOT to use this skill

- ❌ Designing an agent's controls before anything has gone wrong — `agent-threat-model`
- ❌ Setting token, spend or loop limits ahead of time — `agent-budget`
- ❌ Reviewing an agent's settings, permissions or MCP config when nothing has gone wrong — `agent-config-review`
- ❌ Writing the customer status page or stakeholder update — `incident-comms`
- ❌ The blameless write-up once it's contained — `postmortem-generator`
- ❌ A standing procedure for credential rotation or on-call — `runbook-generator`

## Anti-patterns to avoid

- ❌ **Opening with process** when the person asked "is it gone?" or "is my fix enough?"
- ❌ **Force-pushing or deleting first.** The key is already in clones, PR refs and the CI log.
- ❌ **Running a loop bill as a breach,** or a second unexplained caller as a loop.
- ❌ **"Restore from backup"** with no restore point, deadline, target instance or caveats.
- ❌ **Skipping the local recovery path** for a force-push: the reflog is the fastest way back.
- ❌ **Showing the machinery.** No skill names, paths or script names in the reply.
