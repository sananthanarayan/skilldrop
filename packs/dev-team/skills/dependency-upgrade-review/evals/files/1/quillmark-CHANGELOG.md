# quillmark changelog

## 4.1.0 (2026-09-02)

- Added: optional native syntax highlighter `quill-native-highlight`, installed as an optional dependency. Its install script downloads a prebuilt binary for the current platform and falls back to the JavaScript highlighter when the download fails.
- Fixed: tables with an empty header cell rendered an extra column.

## 4.0.1 (2026-08-11)

- Fixed: `render()` threw on input with CRLF line endings.

## 4.0.0 (2026-07-28)

### Breaking

- `renderInline()` is removed. Use `render(src, { inline: true })`.
- The `sanitize` option now defaults to `false`. Raw HTML in the input is passed through to the output unless `sanitize: true` is set on the call or through `setOptions()`.
- Node.js 18 is the minimum supported version.
- The `html-escape-lite` dependency is dropped; escaping now uses `entity-codec` 3.

## 3.5.0 (2026-05-19)

- Security: a link title containing `"` could close the `title` attribute and inject markup. Fixed in 3.5.0; affects 3.0.0 to 3.4.x.
- Deprecated: `setOptions()` (global options). Pass options to each `render()` call instead. `setOptions()` will be removed in 5.0.
