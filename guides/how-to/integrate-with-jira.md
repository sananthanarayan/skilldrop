---
title: Use skilldrop with Jira
summary: Feed Jira tickets and epics into skilldrop skills — bug triage, story splitting, implementation loops, and release notes.
kind: how-to
---

# Use skilldrop with Jira

skilldrop has no Jira API integration — it works with text you paste or have your agent retrieve via an MCP server. The patterns below show exactly what to copy and what to say.

## Bug triage from a Jira ticket

Copy the ticket's summary, description, steps to reproduce, and environment fields. Then:

```
Here is a Jira bug ticket:

Summary: [paste]
Description: [paste]
Steps to reproduce: [paste]
Environment: [paste]

Run bug-triage.
```

`bug-triage` returns a severity assessment, a root-cause hypothesis, and a recommended next step. Paste that back into the Jira ticket as a comment or into a linked Confluence page.

## Story splitting from an epic

Copy the epic's goal and any child stories already defined. Then:

```
Here is a Jira epic:

Goal: [paste epic summary and description]
Existing stories: [paste titles, or "none yet"]

Run user-story-splitter.
```

The skill returns independently shippable slices with acceptance criteria for each. Create one Jira sub-task per slice, using the acceptance criteria as the Definition of Done.

## Implementation from a story

Take one Jira story and its acceptance criteria. Reference the ticket ID so the session output is traceable:

```
Jira ticket: PROJ-123
Title: [paste story title]
Acceptance criteria:
- [paste each criterion]

Run feature-implement-loop.
```

`feature-implement-loop` treats the acceptance criteria as its gate — each checkpoint confirms criteria are still being met before the next iteration starts. When done, link the resulting PR back to PROJ-123.

## Release notes from a sprint

At the end of a sprint, export the completed issues list (Jira's sprint report has a "Copy" option, or use `jira sprint list --completed`). Then:

```
Here are the completed Jira tickets from sprint 42:

PROJ-101: [title]
PROJ-108: [title]
PROJ-115: [title]

Run release-notes.
```

`release-notes` groups changes by type and writes a changelog entry. Copy the result into your release ticket or Confluence release page.

## Using the Jira MCP

If the Jira MCP is installed in Claude Code, you can ask the agent to fetch ticket text directly instead of copying:

```
Fetch PROJ-123 from Jira and run bug-triage on it.
```

The agent retrieves the ticket and passes it to the skill inline.
