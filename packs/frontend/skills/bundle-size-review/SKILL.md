---
name: bundle-size-review
description: Find what makes a JavaScript bundle heavy and what can safely come out, from the bundler's stats file (webpack stats.json, an esbuild metafile, or the rollup-plugin-visualizer raw-data JSON that Vite builds use) read together with the repo around it (package.json, .browserslistrc, the lockfile, the bundler config and the source files that import the heavy modules). Gives each entry's first-load JavaScript in the exact bytes the stats record, kept apart from lazy chunks; finds whole-library imports, CommonJS packages that can't be tree-shaken, packages bundled twice and polyfills the browser targets don't need; names the import chain that pulls each module in before suggesting a removal; and, given before and after stats, says what grew, why, whether it lands in the first load and which per-entry budget would have caught it. Use when the user says "why is our bundle so big", "what can we cut from the bundle", "review this stats.json", "why is lodash or moment in our bundle", "the bundle grew in this PR", or "set a bundle size budget".
---

# bundle-size-review

Reads the bundler's own record of what it built, and the repo files that decide what it should have built, and answers two questions: what does the browser download before the first screen, and which of it can come out without breaking something. The stats file and the repo are the evidence; an analyzer treemap and `du -sh node_modules` are not. Page-load performance from a Lighthouse report (LCP, INP, CLS) is `web-performance-review`; choosing how a route is rendered is `rendering-strategy`. Whether to merge a dependency bump is `dependency-upgrade-review`; reviewing the code change itself is `pre-merge-review`.

## How to respond

**Four rules come before the steps and outrank them:**

- **Answer what was asked, first.** Open with the answer, the decision or the artifact, in plain words. Scores, matrices, frameworks and tags come after it, and anything that doesn't change the answer is cut.
- **Use only what you were given.** Don't add facts, names, numbers, incidents, history, steps or sections the input doesn't contain. What you need and don't have is left out of the artifact and listed once at the end under "To confirm".
- **Deliver from what you have.** When the request gives you something to work on, state your assumptions in a line and produce the result. When it gives you nothing to work on, ask for it in one or two plain sentences and say what you will do once you have it.
- **Write for someone who has never heard of this skill.** No skill names, no paths or scripts from this folder, no internal terms, and nothing about how the run was set up. A next step is one plain sentence at the end that describes the work.
- **For this skill:** The repo outranks the stats file on what the build is for, and nothing is called missing without having been looked for. Browser targets, installed versions and how a module is imported live in the files next to the stats; read them, cite them, and rank every fix by what the first screen waits for.

1. **Get the stats file, asking once.** One of: webpack `stats.json`, an esbuild metafile, or rollup-plugin-visualizer output with `template: "raw-data"` (Vite). A treemap screenshot is not enough. Ask for the file with the command that makes it:
   ```bash
   npx --no webpack --mode production --json=stats.json
   npx --no esbuild src/main.tsx --bundle --minify --splitting --format=esm --outdir=dist --metafile=meta.json
   ```
   For Vite, the visualizer config is in [`reference.md`](reference.md).

2. **Run the script before reading anything by hand.** It sizes every entry's initial JavaScript and each lazy chunk, lists the largest modules and packages, finds packages installed at more than one path, flags whole-library CommonJS imports, locales and polyfills, prints the chain for each `--why`, and reads the project around the stats file (the stats folder, its parent or grandparent, or `--root`):
   ```bash
   # Claude Code
   python3 "${CLAUDE_SKILL_DIR}/scripts/bundle_stats.py" stats.json --why lodash --budget main=320kB
   # Other IDEs (from the skill folder)
   python3 scripts/bundle_stats.py stats.json --why lodash --budget main=320kB
   ```
   `--compare before.json after.json` diffs two builds; `--dist dist/` gzips the built files so compressed sizes are measured; `--json` for machine output; `-` reads stdin. Exit 1 means a budget failed, 2 bad input. With no script runtime, follow the field-by-field method in [`reference.md`](reference.md) and show the arithmetic.

3. **Read the repo before concluding anything about it.** The script's "Project files" block lists what it found and what is absent: `package.json` (ranges, `browserslist`), `.browserslistrc`, the lockfile, `webpack.config.*` / `vite.config.*` / `build.mjs` (`target`, existing budgets), `tsconfig.json` (`target`), and the source files that import each bundled package. Open the source files named in the chains and the configs it lists, and cite them by name in the reply. A claim that a file does not exist comes only after listing the folder (`ls -a`, a glob), and is worded as what was looked for.
   - ✅ *"`.browserslistrc` targets Safari 15 and Chrome 100, and `vite.config.ts` builds for `safari15`, so four of the five polyfills in `src/setup/polyfills.ts` are dead."*
   - ❌ *"There is no browserslist, so the polyfills can't be judged."* (said without looking; the file was there)

4. **Lead with the exact sizes the stats give, and say which size it is.** Copy the bytes from the stats, never round them into a new figure first. One unit system for the whole reply: bytes, with kB = 1000 bytes for readability (*"288,640 bytes (288.6 kB)"*); no KiB, KB or MB mixed in. Say once what the number is: webpack module `size` is before minification; a webpack asset size is the emitted file, minified and uncompressed; esbuild `bytes` and `bytesInOutput` are post-bundle (minified when `--minify` is on), uncompressed; the visualizer gives rendered length, plus gzip and brotli when enabled. Leave `.map` outputs out of every count.
   - **Compressed sizes are secondary and never invented.** Quote them only when measured (the built files under `--dist`, or the visualizer's gzip/brotli). Otherwise give the command that measures them after a build, in plain words: gzip the entry's files with `gzip -9c` and count the bytes with `wc -c`.
   - ✅ *"The `app` entry is 288,640 bytes of minified JavaScript before compression (esbuild output bytes)."* ❌ *"app is about 92 KB gzipped"* (no built files were given: that number is a guess).

5. **Separate initial from lazy, then rank.** Order: (a) what can come out of or shrink in the initial chunks, (b) duplicates in the initial chunks, (c) lazy chunks last, each named with the route that loads it. ✅ *"monaco-editor is the biggest library (2,104,300 bytes), but only `routes/Editor.tsx`, loaded with `import()`, pulls it in, so it does not delay the first screen."* ❌ *"Replace monaco-editor first, it is the biggest dependency."*

6. **Name why a module is there before suggesting it go.** Give the chain from the entry and whether the app imports it directly or a dependency does. A transitive module does not leave when its line leaves `package.json`. Read the importing source file when it is on disk: `import * as Flags from "worldflags"` read as `Flags[code]` keeps every export, and the fix is explicit imports or a code-to-component map of the ones in use (found with a search for `<Flag code=` when the callers aren't given).

7. **Find what tree-shaking failed to remove.** Patterns, replacements and what to check are in [`reference.md`](reference.md): whole-library CommonJS imports (`import _ from "lodash"`), barrel files and namespace imports, CommonJS packages in initial chunks (a prebuilt `react-dom.production.min.js` is not a finding), side-effectful modules, locale bundles.
   - **Polyfills against the targets:** the script checks each bundled core-js module against the browser targets it found and lists the files that use a still-needed feature. Drop the polyfills every target has natively; keep any feature a target lacks that the code uses, and name the file. ✅ *"Keep `es.array.find-last`: Safari 15 lacks `Array.prototype.findLast` (it arrived in 15.4) and `src/lib/history.ts` calls it; the other four can go (4,210 bytes)."* With no targets in any file, this goes under To confirm.

8. **Make every fix safe for the installed versions.** Read the installed version (lockfile) and declared range (`package.json`) before naming an API, an import path or a version. Never suggest a downgrade, an option or an export the installed major doesn't have, or a flag the tool doesn't take. For a duplicate, name both install paths, each version and who asks for which range (the script reads them from the lockfile; without one, give `npm ls <package>`). Forcing one copy with `overrides` across a major version is a change to test, not a free removal; whether a newer dependent accepts the newer major is checked with network access, never asserted:
   ```bash
   npm view @harbor/calendar versions
   npm view @harbor/calendar@latest dependencies
   ```
   ✅ *"@harbor/calendar 2.3.0 asks for date-fns ^2.29.0 while the app uses 3.6.0, so two copies ship (18,400 + 5,200 bytes). An override to 3.x is a major jump for the calendar; check with `npm view` whether a calendar release accepts date-fns 3 first."* ❌ *"Upgrade the calendar to 3, which uses date-fns 3"* (not in the input) or *"pin date-fns to 2.x"* (downgrades the app).

9. **For before and after, attribute the growth.** Run `--compare`. Lead with the change in each entry's initial JavaScript, then the lazy chunks; name the modules that moved and the chain that brought them; call out anything that moved from lazy to initial. When someone compared totals, show both numbers side by side: the total barely moved because bytes changed place.

10. **Set or check a budget per entry.** The guard is a limit on each entry's initial JavaScript, not on the total. Pick a threshold between the good build and the bad one (the current figure plus about 5%, or the team's target), in the same unit as the tool that enforces it: webpack `performance` with `hints: "error"` and `maxEntrypointSize` counts emitted bytes, minified and uncompressed; size-limit measures compressed size from the built files itself. When the stats carry pre-minification module sizes, say the emitted figure comes from one build before fixing the number. State that a total-size limit misses a lazy-to-initial move and fails on harmless lazy growth.

11. **Reply short, in one message, in this order.**
    - **First line answers the question in the person's words.** ✅ *"Yes, the reviewer is right: echarts moved from the lazy reports chunk into vendors, so the first load grew from 311,282 to 803,674 bytes (+492,392) while the total fell 1,949."* ❌ *"This confirms it."* / *"Let me break this down."*
    - **Then the fixes, numbered by first-load impact:** what it is, the chain, the change, what to check after. Two to four lines each.
    - **One line on lazy chunks** when they matter to the question.
    - **Then the guard:** the per-entry budget that would have caught it, with its threshold.
    - **"To confirm"** for what only the user can answer; omit it when empty. No module tables, no full package lists, no tool output pasted in, no flags or options that don't exist. About 250 words.

**Non-interactive runs** (subagent, CI, headless): with no stats file, emit `BLOCKED: need the bundler stats file (webpack --json, esbuild --metafile, or rollup-plugin-visualizer raw-data)`. With only built files or a treemap screenshot, report the per-file sizes and emit `BLOCKED: need the stats file to say what is inside each chunk`. Browser targets absent from every project file (after looking) become `[assumption] browser targets unknown; polyfill findings unconfirmed`; a missing budget becomes `[assumption] budget set at the current initial size plus 5%`.

## Useful references in this skill

- [`reference.md`](reference.md): producing stats for each bundler, what each format's sizes mean, the project files read and how, replacements for the usual heavy packages with what to check, duplicates and versions, budgets in CI
- [`scripts/bundle_stats.py`](scripts/bundle_stats.py): stdlib reader for webpack, esbuild and visualizer stats plus the project around them; bytes throughout, chains, duplicates with lockfile versions, polyfills against targets, `--compare`, `--budget` (exit 1 over budget, 2 bad input)
- [`examples/larkspur-sparkline.md`](examples/larkspur-sparkline.md): worked example, a PR that moved a chart library from a lazy chunk into the first load while the total stayed flat

## Quality bar

- **The first line answers the question** in the person's terms, with the exact byte figures from the stats.
- **The repo was read:** targets, versions and importing files are cited by file name; nothing is called absent without having been looked for.
- **One unit system,** bytes with kB = 1000, and the kind of size (module, emitted, post-bundle, compressed) is named once.
- **Compressed figures are measured or absent,** never estimated into the lead.
- **Initial and lazy are kept apart,** and a lazy chunk is never ranked above an initial-chunk fix.
- **Every suggested removal names its import chain** and is valid for the installed version; no downgrades, no APIs the installed major lacks.
- **Duplicates name both paths, both versions and who asks for which range,** and a major-version override is flagged as a change to test.
- **A per-entry budget closes the reply,** with a threshold that passes the good build and fails the bad one.

## When to use this skill

- ✅ "Why is our bundle so big?" with a webpack, esbuild or Vite stats file
- ✅ A PR made the bundle grow and someone wants to know what and why, from before and after stats
- ✅ "Why is lodash / moment / core-js in our bundle?" or "can we drop this package?"
- ✅ Two versions of a package in the bundle, or one module in several chunks
- ✅ Setting or checking a bundle size budget per entry in CI

## When NOT to use this skill

- ❌ Reading a Lighthouse report for what slows the page (LCP, INP, CLS, render-blocking requests): use `web-performance-review`
- ❌ Choosing SSR, static or client rendering per route to ship less JavaScript: use `rendering-strategy`
- ❌ Deciding whether a dependency bump PR is safe to merge: use `dependency-upgrade-review`
- ❌ Reviewing the application code in a PR for correctness: use `pre-merge-review`
- ❌ Server or API response time, database queries, or backend memory

## Anti-patterns to avoid

- ❌ **"There is no browserslist" without listing the folder.** `.browserslistrc`, `package.json` and the build config's `target` all name targets.
- ❌ **Leading with estimated gzip numbers.** The stats give exact bytes; lead with those.
- ❌ **Mixing KB, KiB and MB.** Pick bytes and kB = 1000 and keep them.
- ❌ **Leading with the biggest package.** The biggest is often behind a route nobody opens on the first screen.
- ❌ **Adding up every chunk, or counting `.map` files.** The first load is the entry's initial chunks.
- ❌ **"Remove X" without the chain,** or a fix the installed version can't take.
- ❌ **Forcing a nested copy to the app's major and calling it safe.**
- ❌ **A total-size budget as the only guard.** It misses a lazy-to-initial move.
- ❌ **Openers and leftovers:** "This confirms it", pasted tool output, flags that don't exist.
