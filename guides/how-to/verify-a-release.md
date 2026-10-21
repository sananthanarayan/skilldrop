---
title: Verify a release
summary: Check that a skilldrop-cli release came from this repository's release workflow, unchanged, using npm's provenance, the GitHub attestation on the release tarball, and its SBOM.
kind: how-to
---

# Verify a release

You can check that the `skilldrop-cli` package you install was built by this repository's release workflow, from a commit on `main`, and wasn't changed on the way. Every release from 0.16.40 on carries three things: npm provenance, a Sigstore-signed attestation for the tarball on its GitHub Release, and a CycloneDX SBOM.

## Check the package npm installed

In a project where you've installed `skilldrop-cli`, run:

```bash
npm audit signatures
```

npm checks the registry signature on every installed package and, for `skilldrop-cli`, the provenance statement. That statement says the package was published by GitHub Actions from `sananthanarayan/skilldrop`. A failure names the package that didn't verify.

## Check a release tarball

Download the tarball from the [release page](https://github.com/sananthanarayan/skilldrop/releases), or with the GitHub CLI:

```bash
gh release download v1.0.0 --repo sananthanarayan/skilldrop --pattern 'skilldrop-cli-1.0.0.tgz'
```

Then verify its attestation:

```bash
gh attestation verify skilldrop-cli-1.0.0.tgz --repo sananthanarayan/skilldrop \
  --signer-workflow sananthanarayan/skilldrop/.github/workflows/release.yml
```

It succeeds only if the file was signed by the release workflow on this repository. The same file is attached to the release as `skilldrop-cli-1.0.0.tgz.sigstore.json`, if you'd rather check it with another Sigstore tool.

To confirm the tarball is the one npm serves, compare their hashes:

```bash
npm view skilldrop-cli@1.0.0 dist.integrity
echo "sha512-$(openssl dgst -sha512 -binary skilldrop-cli-1.0.0.tgz | base64)"
```

The two lines match when they're the same file.

## Read what's inside

The release's `skilldrop-cli-<version>.cdx.json` is a CycloneDX SBOM of the package. The CLI has no runtime dependencies, so it lists the package alone. A tool that reads CycloneDX, such as a dependency scanner, can take it as it is.

## Related

- [Versioning and what stays stable](../reference/versioning-and-stability.md)
- [SECURITY.md](../../SECURITY.md): how to report a vulnerability
