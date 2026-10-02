# Packaging beyond npm

npm (`npx skilldrop-cli`) is the main channel and publishes from CI. PyPI carries the same
files, so it follows each npm release. It needs a one-time setup that only the maintainer can do.

## PyPI

`pipx install skilldrop-cli` once it's published. The wheel carries the npm package's files
and a small Python launcher that runs them with `node`, so Node 16.7+ is still needed. It's
there for people whose tooling starts from pip or pipx.

One-time setup:

1. Create an account on [pypi.org](https://pypi.org/account/register/) and turn on 2FA.
   `skilldrop-cli` was not yet taken on 2026-10-01.
2. Create an API token scoped to the project after the first upload. Before then, the token
   has to be account-wide.

Each release:

```bash
python3 -m pip install build twine
python3 packaging/pypi/build_wheel.py            # dist/skilldrop_cli-<version>-py3-none-any.whl + sdist
python3 -m twine upload dist/*
```

Publishing from CI is set up and waiting. The `pypi` job in
[`release.yml`](../.github/workflows/release.yml) builds the wheel and uploads it with PyPI
trusted publishing (OIDC, no stored token) whenever `package.json`'s version is not yet on PyPI.
It stays off until two things are done, after the first manual upload has created the project:

1. On pypi.org, open the `skilldrop-cli` project, then Publishing, and add a GitHub publisher:
   owner `sananthanarayan`, repository `skilldrop`, workflow `release.yml`, environment blank.
2. In the GitHub repository, set the Actions variable `PYPI_PUBLISH` to `true`.

From then on a version bump publishes to npm and PyPI, and the manual steps above are only a
fallback.
