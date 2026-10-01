# Roadmap

What is being worked on next. Not a commitment — a direction. Shipped work moves to [CHANGELOG.md](CHANGELOG.md).

## Upcoming

- **MCP integration guide** — how to combine skilldrop skills with Claude Code MCP servers; which skills pair naturally with the Figma MCP, Linear MCP, and GitHub MCP
- **Commit-pinned third-party catalogs** — record the resolved commit SHA in the ledger, and warn when `update` sees new content under an unchanged version (OWASP AST02, AST07; see [the OWASP mapping](guides/reference/owasp-mapping.md))
- **A permission manifest for skills** — declare network, shell and filesystem needs, so `skilldrop scan` can compare what a skill says with what it does (AST03, AST10)
- **Homebrew tap and PyPI release from CI** — publishing both channels with the npm release; the formula and wheel builder are in [`packaging/`](packaging/README.md)
