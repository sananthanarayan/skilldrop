# Key in a commit: my notes (Tue 14 Oct 2026, times are CEST)

- 09:12 The coding agent (runs on our shared build box `bx-02` in a tmux session) committed
  `deploy/env.sh` to branch `agent/summariser-retry` in tallowbank/ledgerline-api. Commit
  3f9c2a1. The file has our Anthropic API key in clear (starts `sk-ant-api03-EXAMPLE`, ends `7Qx2`).
- 09:15 Agent pushed the branch and opened PR #482. CI ran on the PR.
- 16:40 I spotted the key while reviewing PR #482.
- The repo is private. About 30 people in the org can read it.
- The same key is the one the production summariser uses (it's in our prod secret store).
  Rotating it means a prod config change and a restart of the summariser service.
- The agent session on bx-02 is still running. It's waiting on review comments.

## My plan

1. Force-push the branch to drop commit 3f9c2a1, and close PR #482.
2. Rotate the key tomorrow morning in the 08:00 deploy window, so prod isn't disrupted.
3. Tell my lead on Thursday at our 1:1.

Is this right, or am I missing something?
