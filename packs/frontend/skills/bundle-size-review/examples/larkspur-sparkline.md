# Worked example: a chart library moves into the first load while the total stays flat

## Input

> PR #241 on larkspur-dispatch-web adds a small jobs-per-hour sparkline to the dashboard header. Our CI checks that total JS stays under 850 KB and it passed. A reviewer says the dashboard feels slower to open. Before and after webpack stats are attached (`inputs/stats-before.json`, `inputs/stats-after.json`). Did this PR make the first load heavier?

## What the script printed (abridged)

```bash
python3 scripts/bundle_stats.py --compare examples/inputs/stats-before.json examples/inputs/stats-after.json --budget main=330kB
```

```text
Chunk sizes: emitted asset bytes (after minification, before compression).
Module and package sizes: webpack module size, before minification.
Compressed sizes: not measured; no built files were read (pass --dist DIR after a build).

All JS chunks: 812,606 B (812.6 kB) -> 810,657 B (810.7 kB) (-1,949 B); initial +492,392 B, lazy -494,341 B

Initial JS per entry
  main: 311,282 B (311.3 kB) -> 803,674 B (803.7 kB) (+492,392 B)

Chunks that changed
  reports    lazy       498,212 B ->   3,871 B (-494,341 B) changed; loaded with import() from src/routes.js
  vendors    initial    301,412 B -> 792,840 B (+491,428 B) changed
  main       initial      9,870 B ->  10,834 B (+964 B) changed

Packages that changed (sorted by change in initial size)
  echarts   total 503,088 B -> 503,088 B (0 B); initial 0 B -> 503,088 B (+503,088 B) changed
      chain: src/index.js > src/App.jsx > src/components/JobsSparkline.jsx > node_modules/echarts/index.js
  zrender   total 167,660 B -> 167,660 B (0 B); initial 0 B -> 167,660 B (+167,660 B) changed
  moved from lazy to initial: echarts, zrender

Project files (root: examples/inputs)
  found: (none)
  absent: package.json, .browserslistrc, bundler config (webpack/vite/rollup/esbuild config, build.mjs), lockfile
  bundled source files not on disk here (9): src/App.jsx, ..., src/components/JobsSparkline.jsx, ...

Budgets on each entry's initial JS, before -> after
  main: budget 330,000 B (raw); before 311,282 B (PASS), after 803,674 B (OVER)
```

## Reply

Yes, the reviewer is right: the first load went from 311,282 to 803,674 bytes of JavaScript (+492,392), while the total fell by 1,949 bytes, which is why the 850 KB total check passed. The new `JobsSparkline.jsx` imports echarts directly, and that pulled echarts and zrender out of the lazy `reports` chunk (498,212 → 3,871 bytes) into `vendors`, which every page loads before the first screen. Sizes are webpack's emitted files, minified and before compression; no built files were attached, so there is no compressed figure here.

1. **Load the sparkline's chart code on demand.** Chain: `src/index.js` → `App.jsx` → `components/JobsSparkline.jsx` → `echarts`. Render the header without the sparkline, then `import("echarts/core")` inside the component and draw once it resolves. Check the reports page still opens its charts, and that the header doesn't jump when the sparkline appears (reserve its height).
2. **Register only the line chart.** The bare `echarts` import brings every chart type and component; the moved modules include geo, dataZoom and bar views that a line sparkline never draws. Switch to `echarts/core` with `use([LineChart, GridComponent, CanvasRenderer])` plus what the reports page draws; open every report chart afterwards, since an unregistered type fails at runtime. Confirm the installed echarts is 5.x first (no `package.json` was attached), since `echarts/core` arrived in 5.

**Guard:** a per-entry limit on `main`'s initial JavaScript would have failed this PR: webpack `performance: { hints: "error", maxEntrypointSize: 330000 }` passes today's 311,282 bytes and fails 803,674. The total-size limit can't see a lazy-to-initial move; keep it, but add the per-entry one.

To confirm: whether the sparkline has to show on first paint. If it does, a plain SVG path drawn from the hourly counts needs no chart library at all.
