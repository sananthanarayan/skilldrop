# API builder

Skills for teams building on the Anthropic API — prompt caching, token budgeting, eval generation for skills, and tool-use schema writing.

`/plugin install api-builder@skilldrop` · generated from [`main`](https://github.com/sananthanarayan/skilldrop) — do not edit.

## Start here: Find where prompt caching will cut your input costs

Paste this into Claude Code:

```text
Here is our system prompt and a typical request: <paste them>. Where should the cache_control breakpoints go, and what hit rate should we expect?
```

- **Before you start:** A system prompt and a typical request from your Claude API integration
- **How to tell it worked:** prompt-caching-advisor marks where each cache_control checkpoint goes and estimates the cache hit rate.
- **If nothing happens:** If prompt-caching-advisor does not activate, ask for it by name and check that its folder exists in your skills folder (`~/.claude/skills/` by default).

## Skills

- `eval-harness-generator`
- `prompt-caching-advisor`
- `token-budget-estimator`
- `tool-use-schema-writer`

More: https://sananthanarayan.github.io/skilldrop/packs/api-builder/
