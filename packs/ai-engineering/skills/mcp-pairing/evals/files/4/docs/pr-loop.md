# Our agent PR loop

The coding agent runs this loop for every ticket in the "Agent-ready" Jira column.

1. **Pick up** - read the Jira ticket (description, acceptance criteria, linked tickets). Move it to "In Progress".
2. **Implement** - branch off `main`, write the change and tests, push the branch, open a draft PR on GitHub.
3. **Review** - a second agent session reads the PR diff, the CI results and the ticket, and decides if it meets the acceptance criteria.
4. **Merge gate** - a human tech lead approves and merges. Nothing merges without a human.
5. **Announce** - post a one-line summary with the PR link to `#team-orders-dev` in Slack.

Repo: one GitHub repo, `example-org/orders-service`. CI is GitHub Actions.
The `.mcp.json` lives in the repo root and is committed so everyone gets the same setup.
