# PR #318: Export orders to CSV, heatmap on Analytics

- Adds an "Export CSV" button to the orders toolbar (`src/components/ExportButton.tsx`, rendered by `src/components/Toolbar.tsx`). Uses `papaparse` to build the CSV and `file-saver` to download it.
- Adds a weekday-by-hour order heatmap to the Analytics page (`src/routes/Analytics.tsx`) using `@tidal/heatmap`.

## CI

- build: passed
- unit tests: passed
- bundle-size: **failed**

```
bundle-size: total size of dist/*.js must be <= 1,400,000 bytes
  before (main @ 4e1a7c2): 1,255,206 bytes
  after  (this PR):        1,474,530 bytes
FAILED: over by 74,530 bytes
```

## Author comment

> The heatmap library is big but it's only on the Analytics route, which is lazy-loaded. I'd like to raise the bundle-size limit to 1.6 MB so this can go in.
