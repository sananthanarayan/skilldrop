# Release notes copied from the two action repositories

## northwind-ci/checkout-lite

### v3.2.0

- Added: `sparse-paths` input for partial checkouts.
- Changed: the action now runs on the Node 24 runtime. Self-hosted runners need runner version 2.330.0 or later.

### v3.1.1

- Fixed: `fetch-depth: 0` timed out on repositories with more than 50,000 tags.

## octo-tools/pypi-publish

### v3.0.0

- Breaking: trusted publishing (OIDC) is now the default. A job that does not pass `password` needs `permissions: id-token: write`.
- Deprecated: the `password` input. It still works in v3 and is removed in v4.
- Changed: `verify-metadata` now defaults to `true`; an upload with an invalid long description fails instead of warning.
