// Publishes the built bundle and a signed provenance manifest.
// Run only from .github/workflows/release.yml on a version tag.
import { createNotary } from "release-notary";
import pkg from "../package.json" with { type: "json" };

const notary = createNotary({
  // legacyMode keeps the v1 manifest layout that the downstream
  // ledger-portal deploy script still parses.
  legacyMode: true,
  signingKey: process.env.RELEASE_SIGNING_KEY,
});

await notary.publish({
  name: pkg.name,
  version: pkg.version,
  dir: "dist",
  sign: true,
});
