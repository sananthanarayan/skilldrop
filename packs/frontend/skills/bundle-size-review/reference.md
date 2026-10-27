# bundle-size-review reference

## Producing the stats file

webpack 5 (webpack-cli 4 or later writes the JSON straight to the file, so build logs cannot corrupt it):

```bash
npx --no webpack --mode production --json=stats.json
```

esbuild, from the CLI or from `esbuild.build({ metafile: true })` with `result.metafile` written to a file:

```bash
npx --no esbuild src/main.tsx --bundle --minify --splitting --format=esm --outdir=dist --metafile=meta.json
```

Vite or Rollup: add rollup-plugin-visualizer with the raw-data template, then run the normal build. `gzipSize` and `brotliSize` make the plugin record compressed sizes per module, which beats an estimate.

```js
// vite.config.js
import { visualizer } from "rollup-plugin-visualizer";
export default {
  plugins: [visualizer({ filename: "stats.json", template: "raw-data", gzipSize: true, brotliSize: true })],
};
```

Keep the built folder (`dist/`) next to the stats and pass it with `--dist`: the script then gzips the real emitted files (level 9). Without it, no compressed size is printed.

## What each format carries, and what its sizes mean

| Format | Detected by | Raw size of a chunk | Module size | Initial vs lazy | Importers |
|---|---|---|---|---|---|
| webpack stats | `assets`, `chunks`, `modules`, `entrypoints` | emitted asset bytes, after minification (`assets[].size`) | `modules[].size`, **before minification** | `chunks[].initial`; an entry's chunks are `entrypoints.<name>.chunks` | `modules[].reasons[].moduleName`, with `type` (`import()` = lazy) and `userRequest` |
| esbuild metafile | `inputs` and `outputs` objects | `outputs[].bytes`, minified if `--minify` was on | `outputs[].inputs[].bytesInOutput`, what each input adds to that output | entry outputs have `entryPoint`; their `imports` of kind `import-statement` are initial, `dynamic-import` are lazy | `inputs[].imports[]` with `kind` and `original` |
| rollup-plugin-visualizer raw data | `tree`, `nodeParts`, `nodeMetas` | sum of `renderedLength`, after tree-shaking, before minification unless the plugin runs after the minifier | `nodeParts[].renderedLength`, plus `gzipLength` / `brotliLength` when enabled | modules reached from an `isEntry` module by static imports are initial; `imported[].dynamic` marks lazy | `nodeMetas[].importedBy` |

Consequences for the reply:

- Quote these bytes exactly, in one unit system: bytes, with kB = 1000 bytes beside them. Name the kind once ("webpack module sizes, before minification"; "esbuild output bytes, minified, uncompressed").
- A webpack stats file without `assets` has no emitted sizes: each chunk's size is the sum of its module sizes, before minification. Say so; the emitted figure comes from a build.
- webpack module sizes and visualizer rendered lengths rank modules; they are not the download. The saving from a removal is measured by rebuilding and running `--compare`.
- Prebuilt production files (`react-dom.production.min.js`) are already minified, so their module size is close to what ships.
- esbuild lists `.js.map` outputs beside the code; they are not downloaded by users and stay out of every count.

## Compressed sizes

| Basis | Where it comes from | How to word it |
|---|---|---|
| built-file | the emitted files under `--dist`, gzipped at level 9 | "measured from the built files" |
| visualizer | sum of the plugin's per-module gzip / brotli lengths | "from the visualizer"; slightly above the whole-file figure, because each module is compressed alone |
| none | no built files and no visualizer gzip | no figure. Say how to measure it after a build: gzip the entry's `.js` files at level 9 (`gzip -9c`) and count the bytes (`wc -c`) |

A ratio applied to raw bytes is a guess, and a guess in the lead line reads as a measurement. Leave it out.

## Project files read around the stats

The script picks the project root as the first of the stats folder, its parent and its grandparent that holds `package.json` or `.browserslistrc` (else one with `src/`), or `--root`. It prints what it found and what is absent, so a reply can say "no `.browserslistrc`, no `browserslist` field in `package.json`" only when that is what was looked for.

| File | What it gives | Used for |
|---|---|---|
| `.browserslistrc`, `package.json` `browserslist` | browser queries (the `[production]` section when present) | polyfill check; plain `chrome >= 110` style queries resolve offline, others (`defaults`, `> 0.5%`) need `npx --no browserslist` |
| `webpack.config.*`, `vite.config.*`, `rollup.config.*`, `build.mjs` / `build.js`, `esbuild.config.*` (root, `config/`, `scripts/`) | `target` (esbuild style `chrome110`), `performance.maxEntrypointSize` / `hints` | the targets when no browserslist exists (esbuild lowers syntax, it does not add polyfills); existing budgets |
| `tsconfig.json` | `target` | syntax level only; it never decides polyfills |
| `package-lock.json` / `npm-shrinkwrap.json` (v1 to v3) | installed version per install path, each package's declared ranges | versions of duplicate copies, who asks for which range, API checks before suggesting a fix |
| `yarn.lock`, `pnpm-lock.yaml` | listed, not parsed | read versions with `yarn why` / `pnpm why` |
| source files (outside `node_modules`, `dist`, `build`) | who imports each bundled package, namespace imports read with `X[...]`, which files use a polyfilled feature | the fix lands in a named file |

The polyfill table in the script holds the first browser version with each feature native (MDN browser-compat data) for the common core-js modules. core-js sometimes keeps a polyfill longer to patch a spec bug, so a rebuild confirms each removal. A module outside the table is reported as "check by hand".

## Version-correct fixes

- Read the installed version before naming an API, an import path or an option. `echarts/core` exists from echarts 5; `lodash-es` named imports need an ESM-aware build; `@aws-sdk/client-*` is a different package from `aws-sdk`.
- Never fix a duplicate by moving the app's own range down a major: that is a downgrade of the app.
- `overrides` (npm), `pnpm.overrides` or `resolutions` (Yarn) that force a dependent onto a major it never declared is a change to test by hand, not a free removal. Check whether a newer dependent accepts the newer major, with network access:

```bash
npm view @harbor/calendar versions
npm view @harbor/calendar@latest dependencies
```

## Reading the stats by hand

When no script can run:

1. **webpack:** take `entrypoints.main.assets[]` (or the `files` of each chunk in `entrypoints.main.chunks`), keep `.js`, add their `size` from `assets[]`. That is the initial raw size. Every chunk with `"initial": false` is lazy; its `origins[].moduleName` is the file that loads it.
2. **esbuild:** start at the output whose `entryPoint` is the app entry, follow its `imports` of kind `import-statement` through `outputs`, and add the `bytes` of each. Outputs reached only through `dynamic-import` are lazy.
3. **visualizer:** each top-level child of `tree` is an output file; add `gzipLength` over the `nodeParts` of the files the entry loads statically.
4. **Chains:** from the module, follow its importers (`reasons`, `inputs[].imports` reversed, `importedBy`) until reaching the entry. Prefer the chain with no `import()` step: that is the one that puts it in the first load.

## Replacements for the usual heavy packages

| In the bundle | Change | What to check after |
|---|---|---|
| `lodash/lodash.js` from `import _ from "lodash"` | per-method imports (`import groupBy from "lodash/groupBy"`) or named imports from `lodash-es`; native methods where the targets have them | every importer the stats list; `_.chain(...)` usage, which needs the whole library; that Babel or TypeScript is not compiling ESM imports to `require` |
| `moment` (and `moment/locale/*` or `moment-with-locales`) | date-fns, Day.js, Luxon or `Intl.DateTimeFormat`; to keep moment, drop the locales (webpack: `new webpack.IgnorePlugin({ resourceRegExp: /^\.\/locale$/, contextRegExp: /moment$/ })`, then import the locales in use) | moment objects mutate and the others don't; lenient parsing of non-ISO strings; time zones (moment-timezone); every locale shown to users. If a dependency imports moment, the dependency has to change, not the app |
| `core-js` from `import "core-js/stable"` or `@babel/polyfill` | `@babel/preset-env` with `useBuiltIns: "usage"`, `corejs: 3` and the project's `browserslist`; for Vite, `@vitejs/plugin-legacy` serves polyfills only to old browsers | run `npx --no browserslist` to see the real targets; the features the polyfills cover against those targets |
| full `echarts` from `import * as echarts from "echarts"` | `echarts/core` with `use([...])` for the charts, components and renderer in use | open every chart: a type that is not registered fails at runtime |
| `chart.js/auto` | import the controllers, elements and scales in use and `Chart.register(...)` them | every chart type and plugin |
| `aws-sdk` (v2) in browser code | the modular `@aws-sdk/client-*` packages | that each call's request and error shapes match the v3 client |
| an icon pack or component library through its index | per-path imports, or confirm the package is ESM with `"sideEffects": false` so the index is shaken | the bundle after rebuild: compare with `--compare` |
| a CommonJS package with an ESM build | point the import at the ESM entry (`module` / `exports`) | that the bundler resolves the ESM file (the stats path shows it) |

## Side effects and barrel files

A bundler keeps a module, used or not, when it might have side effects. `"sideEffects": false` in a package's `package.json` (or a list such as `["*.css"]`) tells it that unused re-exports can go. App code has the same problem: `src/components/index.ts` re-exporting forty components, one of which registers something at the top level, keeps all forty. Symptoms in the stats: many modules from one folder or package, all reached through one `index` file, most of them never imported by anything else.

## Duplicates and package managers

- npm hoists one copy to `node_modules/<pkg>` and nests another under `node_modules/<dependent>/node_modules/<pkg>` only when the hoisted version does not satisfy that dependent's range. Two install paths means two versions.
- Versions are in the path only for pnpm (`node_modules/.pnpm/<pkg>@<version>/...`) and Yarn PnP caches. Otherwise read them:

```bash
npm ls date-fns
pnpm why date-fns
yarn why date-fns
```

- To get one copy when the ranges overlap: reinstall so one version satisfies both (`npm dedupe`). When they don't (the dependent wants 2.x and the app 3.x), the options are a newer dependent that accepts 3.x, or an override tested by hand; see "Version-correct fixes".

```bash
npm dedupe
```

- Two copies of React, Vue, or a state library are a bug as well as a size cost (hooks fail with "Invalid hook call", stores split). Name that when it applies.
- The same module in several webpack chunks (not two installs, one module copied) means the split-chunks settings did not extract it to a shared chunk.

## Budgets

A budget is a limit on one entry's initial JavaScript, in the unit of the tool that enforces it. Set it between the good build and the bad one: the current figure plus about 5%, or the team's target. The script checks it on the stats' own bytes, or on measured gzip:

```bash
python3 scripts/bundle_stats.py stats.json --budget main=320kB
python3 scripts/bundle_stats.py stats.json --dist dist/ --budget main=gzip:100kB
```

Exit 1 fails the job. Sizes are bytes or carry a `kB` (1000) or `KiB` (1024) suffix; `--budget '*=320kB'` applies to every entry; repeat `--budget` for several. A gzip budget with no built files is reported as not measured rather than passed.

webpack's own check counts emitted bytes, minified and uncompressed, per entrypoint:

```js
// webpack.config.js
module.exports = { performance: { hints: "error", maxEntrypointSize: 330000, maxAssetSize: 250000 } };
```

When the stats carry only module sizes (no `assets`), read the entry's emitted size from one build before fixing `maxEntrypointSize`. size-limit measures compressed size from the built files itself, so its limit is a compressed figure.

A total-size limit across all chunks is the wrong guard on its own: it passes a change that moves a library from a lazy chunk into the entry (the total stays flat) and fails a change that only grows a route few users open.
