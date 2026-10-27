# Worked example: a Python repo that is TIGHTEN BEFORE USE

## Input

> We're about to roll this Claude Code setup out to the whole data team for tidewater-ingest.
> Anything we should change first?

Files: [`inputs/tidewater-ingest/.claude/settings.json`](inputs/tidewater-ingest/.claude/settings.json),
[`inputs/tidewater-ingest/.mcp.json`](inputs/tidewater-ingest/.mcp.json),
[`inputs/tidewater-ingest/.gitignore`](inputs/tidewater-ingest/.gitignore).

## What the scan listed (abridged, real output)

```text
- allow (4): `Bash(uv run pytest:*)` .claude/settings.json:4; `Bash(make:*)` .claude/settings.json:5;
  `Bash(git diff:*)` .claude/settings.json:6; `mcp__slack__slack_get_channel_history` .claude/settings.json:7
- deny (1): `Read(./.env)` .claude/settings.json:9
- sandbox: allowUnsandboxedCommands = false; enabled = true; excludedCommands = ["docker"];
  network.allowedDomains = ["pypi.org", "files.pythonhosted.org"]
- hooks: PreToolUse [Bash] .claude/settings.json:19: `python3 tools/guard_commands.py`
- `slack` .mcp.json:3: `npx -y slack-mcp-community` - env: SLACK_BOT_TOKEN
- Literal secrets: none found
- [deny-bypassable] Read(./.env) - allowed without asking: Bash(make:*)
- [wide-allow] Bash(make:*)
- [sandbox-escape] docker
- [unpinned-package] npx -y slack-mcp-community
- [hook] python3 tools/guard_commands.py
```

## How it was graded

- Strict sandbox on (`enabled`, `allowUnsandboxedCommands: false`, two package hosts), so `Bash(make:*)` is arbitrary code **inside** a sandbox: 🟧, not 🟥.
- `docker` in `excludedCommands` always runs outside the sandbox: 🟧.
- The Slack server runs outside the sandbox and reads channel history (untrusted: anyone in the channel writes it) with no prompt. Posting is not in `allow`, so it still asks: the prompt is the one control between an injected message and a post. 🟧, held by a person who must see the message body.
- Unpinned `npx -y` package from a publisher the files don't name: 🟧.
- The hook runs a script in the repo, no download: listed, not a finding; its contents are "To confirm".
- No 🟥, four 🟧 → **TIGHTEN BEFORE USE**.

## Output

**TIGHTEN BEFORE USE.** Nothing here runs or leaks without a person seeing it, but four settings
are wider than running tests and reading Slack needs, and two of them sit outside the sandbox.

1. 🟧 `.claude/settings.json:5` — `Bash(make:*)` runs any Makefile target, and `make -f` any file,
   without asking, so the `.env` deny on line 9 doesn't hold: a target can read `.env`. The
   sandbox keeps it inside the project and off the network. Allow the targets the team runs:

   ```json
   "allow": ["Bash(uv run pytest:*)", "Bash(make <target>)", "Bash(git diff:*)"]
   ```

   with one `Bash(make <target>)` per target the team uses.

2. 🟧 `.claude/settings.json:14` — `docker` in `excludedCommands` always runs outside the
   sandbox, with the user's full file and network access. Remove it, and run containers by hand:

   ```json
   "excludedCommands": []
   ```

3. 🟧 `.mcp.json:3` — `npx -y slack-mcp-community` installs whatever version the registry serves
   each time a session starts, outside the sandbox, from a publisher nobody here has named. Pin
   an exact version someone has reviewed, or use Slack's own server if Slack publishes one:

   ```json
   "args": ["-y", "slack-mcp-community@<exact-reviewed-version>"]
   ```

4. 🟧 `.claude/settings.json:7` with `.mcp.json` — channel history is read without asking, and
   anyone in those channels can write instructions into it. Posting still asks, and that prompt
   is the only thing between a planted message and a post: whoever approves must read the
   message body, not just the tool name. Keep any Slack posting tool out of `allow`.

Fine as configured: the strict sandbox and its two hosts, `git diff`, `uv run pytest`, the token
held as `${SLACK_BOT_TOKEN}`, and `.claude/settings.local.json` in `.gitignore`.

**To confirm**
- Each person's `~/.claude/settings.json` and any managed policy: not read, and they add their own allow entries.
- What `tools/guard_commands.py` does: it runs before every shell command.
- The Slack bot token's scopes and which channels it can read.
- The Makefile targets the team runs, to list in `allow`.
