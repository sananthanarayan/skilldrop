---
title: Use skilldrop with Linear
summary: Feed Linear issues, cycles, and projects into skilldrop skills for triage, story splitting, implementation tracking, and release notes.
kind: how-to
---

# Use skilldrop with Linear

skilldrop has no Linear API integration — it works with text you paste or have your agent retrieve via an MCP server. Linear's "Copy issue as markdown" option gives clean, well-structured input for all the patterns below.

## Bug triage from a Linear issue

Open the issue, use "Copy as markdown" (or copy the title, description, and labels), then:

```
Here is a Linear bug report:

[paste issue markdown]

Run bug-triage.
```

`bug-triage` returns a severity assessment, root-cause hypothesis, and next step. Paste the finding into the Linear issue as a comment.

## Story splitting from a project

Copy the project brief or initiative description from Linear's project overview:

```
Here is a Linear project:

Title: [paste]
Description: [paste]
Goal: [paste]

Run user-story-splitter.
```

The skill returns independently shippable slices with acceptance criteria. Create one Linear sub-issue per slice. Use the acceptance criteria as the issue's description and Definition of Done.

## Implementation tracking

Reference the Linear issue ID so the session output is traceable:

```
Linear issue: ENG-204
Title: [paste]
Acceptance criteria:
- [paste each criterion]

Run feature-implement-loop.
```

`feature-implement-loop` uses the acceptance criteria as its checkpoint gate. When the loop ends, add the resulting PR or commit link to ENG-204.

## Release notes from a cycle

At the end of a cycle, copy the completed issues list from Linear's cycle view ("Copy all" exports the issue titles). Then:

```
Here are the completed Linear issues from Cycle 12:

ENG-188: [title]
ENG-195: [title]
ENG-204: [title]

Run release-notes.
```

`release-notes` groups and formats a changelog entry. Paste it into your Linear release project or changelog document.

## Using the Linear MCP

If the Linear MCP is installed in Claude Code, ask the agent to fetch issues directly:

```
Fetch ENG-204 from Linear and run bug-triage on it.
```

The agent retrieves the issue text and passes it to the skill without you copying anything.

See also: [Use skills with MCP servers](use-with-mcp-servers.md)
