# agent-incident-response — reference

Material for the steps in `SKILL.md`. Console areas are named in words because menu labels
move; when the person's console looks different, they search its settings for "API keys",
"tokens" or "credentials".

## Where to revoke, per provider class

| Provider class | Revoke here | Check usage and activity here | Limit spend here |
|---|---|---|---|
| Anthropic API key | Claude Console, the organisation's API keys page under settings: disable or delete the key | The Console's usage and cost pages, filtered to the key or workspace | Workspace or organisation limits in the Console |
| OpenAI API key | The OpenAI platform dashboard, the API keys page for the project (or the organisation's admin keys) | The usage page, filtered by project and key | Project budgets and limits in the project settings |
| GitHub personal access token | The account's settings, developer settings, personal access tokens (classic and fine-grained). Organisation owners can also revoke fine-grained tokens with access to the organisation from the organisation's settings | The organisation's audit log; the account's security log | No spend; restrict token scopes and expiry |
| GitHub App or OAuth app | Suspend the installation, regenerate the private key or client secret in the app's settings; revoke an OAuth grant under the account's applications | The organisation's audit log | — |
| GitHub deploy key or Actions secret | The repository's settings: deploy keys; secrets and variables for Actions (repository and organisation level) | Workflow run history for the window | — |
| AWS access key | IAM, the user's security credentials: deactivate the key, delete it once the replacement works. Temporary credentials already issued from it keep working until they expire: for roles use "revoke active sessions" on the role, otherwise attach a deny policy keyed on token issue time | CloudTrail event history for the window | Billing budgets and alerts; Cost Explorer for the window |
| Google Cloud service account key | IAM and admin, service accounts, the account's keys tab: delete the key | Cloud Audit Logs for the service account | Billing budgets and alerts (alerts, not a hard cap) |
| Azure app secret or storage key | Microsoft Entra ID app registrations, certificates and secrets; for storage, rotate the account keys | The activity log and sign-in logs | Cost Management budgets |
| npm or PyPI token | The account's access tokens page | The package's published versions in the window: each one is an integrity question | — |
| Any other SaaS token or webhook | The service's API keys, tokens or integrations page; regenerate webhook URLs | The service's audit or activity log | — |

**An agent platform that stores provider keys** (a hosted agent console, a team proxy, a
gateway) cannot revoke them. Revoke each one at its provider, then delete it from the platform,
then list every other key stored there: they are all in the same breach.

**Providers sometimes act first.** A key found in a public repo may already be revoked or
quarantined by the provider through secret-scanning partnerships. Check, but never assume it:
a private repo and a CI log are not scanned that way.

## What each leak location keeps after "deletion"

| Where it leaked | What still holds it after the obvious delete |
|---|---|
| A git commit | Every clone and fork; pull-request refs, which the host keeps after a force-push; the host's cached view of the commit by its SHA (ask the host's support to purge it); CI checkouts; other branches and tags that contain the commit; the local reflog |
| A CI log | Everyone with read access to the repository (public repo: everyone); the log retention period; uploaded artifacts and caches. CI masks only values registered as secrets, so a key read from a file or printed by a shell trace is in clear |
| A prompt or transcript | The provider's request logs for their retention period; local transcript files; shared session links; anything the agent wrote out from that context |
| An agent platform or gateway | Whatever it stored: the key, the transcripts, connected tokens |
| Chat, a ticket or an email | Search indexes, notification emails, exports and integrations that mirror the channel |

## Evidence to keep, before any cleanup

- Agent session transcripts and tool-call logs, exported as files
- Shell history on the machine the agent ran on
- CI run logs and artifacts, downloaded before a run is deleted
- The configuration as it was: MCP config, agent settings, hooks, the installed skill or plugin folder
- Install source: package or repository name, the resolved version or commit, the lockfile entry, the install time
- Provider usage and audit exports covering first exposure to revocation
- The commit SHAs, branch names and pull-request numbers involved
- A timeline with every time in UTC and the original zone noted, each line saying where it came from

Store it where the incident responders can read it and the agent cannot. Record keys by prefix
and last four characters.

## Integrity: everything the agent could write

Diff each against the last known-good point, for every repo, project or account the credential
reached, not only the one it was working in:

- Branches and tags created, moved or deleted; the default branch's history (force-pushes)
- Releases and published package versions
- CI workflow files, and the CI secrets and variables
- Repository settings: branch protection, collaborators, deploy keys, webhooks, app installations
- Infrastructure: infrastructure-as-code state, cloud resources created or changed, IAM changes
- Data stores the agent had write access to

## Recovery after a destructive command

Stop all writes to what was hit first. Then, fastest path first:

**Force-push.** The push output `+ <old>...<new> <branch> -> <branch> (forced update)` names the
overwritten tip. Where it still lives, in order of speed:

1. The clone that pushed: `git reflog show origin/<branch>` lists the remote-tracking ref's old
   values; `git reflog show <branch>` lists the local branch's (a `reset --soft` before a squash
   leaves the pre-squash tip there too).
2. Any clone that fetched before the push, above all the overwritten commits' author's: their
   local branch still holds the commits. They must not pull, reset, rebase or run `gc` / `prune`.
3. The host: an open pull request keeps its head commit; some hosts show the forced update in
   the branch's activity and can restore it.

```bash
git cat-file -t <old-sha>                          # "commit" means this clone still has it
git branch recovery/<branch> <old-sha>             # pin it so gc can't take it
git push origin recovery/<branch>                  # on the remote, out of harm's way
git log --oneline <new-sha>..recovery/<branch>     # the commits the force-push removed
```

Then decide with the authors: merge the recovered branch with the squashed work, or put the old
tip back on the branch with `--force-with-lease` naming the current tip. Unreachable commits
survive locally until the reflog expires (90 days by default) and `gc` runs, so pinning a branch
is the step that can't wait.

**Dropped table or database.**

- Restore point-in-time to a **new instance** at a time just before the drop (take the drop time
  from the session log, in UTC). Restoring over the live instance throws away everything written
  since.
- The deadline: the restorable window is the retention period counted back from now, so the
  point before the drop leaves the window at drop time plus retention. A one-day retention means
  start today.
- No point-in-time restore: the newest automated snapshot before the drop; rows written between
  the snapshot and the drop are lost and say so.
- Copy only the dropped tables back from the restored copy into the live database (dump and
  load), then recreate what `CASCADE` removed (foreign keys, views) and reset sequences past the
  highest restored id.
- Delete the temporary instance once the rows are verified (row counts against the copy).
- `deletion_protection = false` and `skip_final_snapshot = true` mean deleting the instance
  itself would leave no way back: say so as the control.

**Deleted files:** editor local history, OS snapshots or backups, and `git fsck --lost-found` for
blobs that were staged.

## Splitting a bill

Group the usage export by key, model and client (user agent) over the incident window only.
Spend that matches the job's configured model, client and schedule is the job; anything else on
the same key is a second caller, and a second caller on a shared or committed key is a possible
compromise until someone owns it. Quote the sums to the cent and the first and last hour of each
group exactly as the export writes them.

## Prompt injection that sent data out

- **Find the injected text** in the transcript: the issue, web page, file, tool result or
  message that carried the instruction. Preserve it, then hide or lock it so the next agent run
  doesn't read it again.
- **Find the way out:** a fetch with data in the URL, a rendered image or link, a pull-request
  or issue comment, an email, a file written to a shared place, a call to the malicious tool.
- **List what was in context** when the instruction arrived: that is what could have left.

## Who to tell, and by when

| Who | When | Why |
|---|---|---|
| Security team or incident lead | Now, before cleanup | They hold evidence and may run their own process |
| The provider | Same day when charges are fraudulent or the provider's platform was the source | Charge review; their logs cover what yours don't |
| Owners of every other repo, project or account in reach | Before their next deploy | Their integrity check is theirs to run |
| Affected customers or users | When their data, code or service may be involved, once the facts are confirmed | Through the normal incident status channel |
| Data protection officer or privacy lead | The same day personal data was in reach | Some laws set short notification clocks (the GDPR's is 72 hours to the regulator) that run from when the organisation became aware; they decide whether the duty applies |
| Legal or compliance | When customer contracts carry security-notification terms | Contract notification windows |

Flag the possible duty and who decides. Do not state whether the duty applies.

## Controls that stop a repeat (pick one or two)

| What happened | The control |
|---|---|
| Key committed or logged | A pre-commit and server-side secret scanner that blocks the push; keys loaded from a secret store, never a file in the repo |
| Key stolen from a platform | Keys scoped to one project with a spend cap; no long-lived keys stored on third-party platforms |
| Runaway bill | A hard spend limit and alert per project; a loop cap on the agent |
| Destructive command | The agent in a sandbox or container; a deny list on force-push, recursive delete and production database commands; branch protection |
| Malicious MCP server or skill | Install only from a reviewed list, pinned to a version or commit; no secrets in the server's env beyond what its job needs |
| Prompt injection | The agent that reads untrusted text holds no credential and no way to send data out |
