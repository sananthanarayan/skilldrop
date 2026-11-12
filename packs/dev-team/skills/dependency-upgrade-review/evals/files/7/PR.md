# chore(deps): update dev dependencies (non-major) #88

**renovate** wants to merge 1 commit into `main` from `renovate/dev-dependencies-non-major`

This PR contains the following updates:

| Package | Type | Update | Change |
|---|---|---|---|
| bundlecrate | devDependencies | minor | `6.0.1` -> `6.1.0` |
| lintwright | devDependencies | minor | `4.2.0` -> `4.3.1` |
| prettyquill | devDependencies | patch | `3.1.2` -> `3.1.4` |
| tsforge-types | devDependencies | patch | `1.4.0` -> `1.4.2` |
| vellum-test | devDependencies | minor | `2.7.3` -> `2.8.0` |

---

### Release Notes

<details>
<summary>bundlecrate/bundlecrate (bundlecrate)</summary>

#### v6.1.0

- **Node.js support:** minimum supported Node.js is now 18.18. Node 16 is no longer tested. (#1502)
- The module resolver has been extracted into its own package, `@bundlecrate/resolver-core`, which `bundlecrate` now depends on. The previous internal fallback package `bundlecrate-legacy-resolver` is no longer needed and has been dropped. No change to resolution behaviour; output is byte-identical on our fixture suite. (#1497)
- Incremental rebuilds are ~20% faster in watch mode. (#1489)

#### v6.0.2

- Fix source-map `sources` paths on Windows. (#1481)

</details>

<details>
<summary>lintwright/lintwright (lintwright)</summary>

#### v4.3.1

- Fix false positive in `no-unused-vars` for destructured catch parameters. (#902)

#### v4.3.0

- New rule `no-floating-promise`, enabled as an error in the `lintwright:strict` preset. It is **not** added to `lintwright:recommended`. (#888)
- `picolabel` updated to 0.9.2 for terminal colour detection fixes.

#### v4.2.1

- Docs-only release.

</details>

<details>
<summary>prettyquill/prettyquill (prettyquill)</summary>

#### v3.1.4

- Fix idempotency bug when formatting long ternaries inside JSX attributes. (#611)

#### v3.1.3

- Performance: cache parsed config across files. (#604)

</details>

<details>
<summary>tsforge/types (tsforge-types)</summary>

#### v1.4.2

- Correct return type of `DeepReadonly<T>` for tuple types. (#77)

#### v1.4.1

- Add JSDoc to `Brand<T, K>`. (#74)

</details>

<details>
<summary>vellum/vellum-test (vellum-test)</summary>

#### v2.8.0

- `vt.legacyTimers()` is deprecated and now prints a warning when called. It still works and will be removed in 3.0. Use `vt.fakeTimers()`. (#455)
- New `expect.toSatisfyAll()` matcher. (#450)

#### v2.7.4

- Fix watch mode ignoring `.mts` files. (#447)

</details>

---

### Configuration

📅 **Schedule**: Branch creation - "before 6am on monday" (UTC), Automerge - Disabled by config.

🚦 **Automerge**: Disabled by config. Please merge this manually once you are satisfied.

---

### Checks

- ci / lint — passed
- ci / format — passed
- ci / typecheck — passed
- ci / test — passed
- ci / build-and-smoke — passed

All checks have passed.
