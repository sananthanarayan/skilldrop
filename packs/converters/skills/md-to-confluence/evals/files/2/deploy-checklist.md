---
title: Deploy checklist v2 (draft)
owner: platform-team
---

# Deploy checklist

Use this list for every production deploy of the storefront. It replaces the version agreed
in March.[^1]

## Before the deploy

- [ ] Release branch is green in CI
- [ ] Database migrations reviewed by a second engineer
- [ ] Feature flags for the release default to **off**
- [ ] Change posted in #deploys with the release number

## During the deploy

| Step | Who | Stop if |
|---|---|---|
| Deploy to canary (5%) | Release captain | error rate above 1% for 5 minutes |
| Deploy to 50% | Release captain | p95 latency above 400 ms |
| Deploy to 100% | Release captain | any page from the storefront rota |

> **Warning:** Do not deploy after 16:00 on a Friday without the platform lead's sign-off.

## After the deploy

- [ ] Watch the storefront dashboard for 30 minutes
- [ ] Turn on the release's feature flags one at a time

[^1]: The March version had no canary step.
