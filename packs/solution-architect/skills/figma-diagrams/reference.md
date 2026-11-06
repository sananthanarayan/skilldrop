# Figma REST API — quick reference

Official docs: https://www.figma.com/developers/api

## Auth

Every request needs the `X-Figma-Token` header:

```
X-Figma-Token: figd_...
```

Tokens are scoped to the user who created them — they can do anything that user can do in the UI.

## Endpoints used by this skill

| Verb | Path | Purpose |
|---|---|---|
| `GET` | `/v1/files/:file_key` | Full file JSON: document tree (pages, frames, all nodes). Large. |
| `GET` | `/v1/files/:file_key/nodes?ids=A,B` | Same shape as above but scoped to specific node IDs — cheaper. |
| `GET` | `/v1/files/:file_key/comments` | List all comments. |
| `POST` | `/v1/files/:file_key/comments` | Add a comment. Body: `{"message": "...", "client_meta": {...}}` |
| `GET` | `/v1/images/:file_key?ids=A,B&format=svg` | Render frames as PNG/SVG/PDF/JPG. Returns S3 URLs (expire ~30 days). |
| `GET` | `/v1/me` | Sanity-check the token. |
| `GET` | `/v1/teams/:team_id/projects` | List projects in a team (needs team-scope token). |
| `GET` | `/v1/projects/:project_id/files` | List files in a project. |

## File key extraction

```
https://www.figma.com/file/AbC123XyZ/My-Architecture
                          ^^^^^^^^^^ <-- FILE_KEY

https://www.figma.com/design/AbC123XyZ/My-Architecture   (newer URL format)
                            ^^^^^^^^^^

https://www.figma.com/board/AbC123XyZ/My-Whiteboard      (FigJam)
                           ^^^^^^^^^^
```

Regex that works on all three: `figma\.com/(?:file|design|board)/([A-Za-z0-9]+)/`

## Node IDs

Nodes have IDs like `1:23` or `1-23` (older URL format used `-`, JSON uses `:`). Both refer to the same node — normalize to `:` when calling the API.

## Rate limits

Roughly **~25 requests/minute per token** for read-heavy endpoints; image renders are slower. The API returns `429 Too Many Requests` with `Retry-After`. Back off, don't hammer.

## Common gotchas

- **`GET /v1/files/:key` is huge** — even small design files can be many MB. Prefer `/nodes?ids=...` if you know the node you want.
- **Image rendering is async on the server.** The endpoint returns synchronously but Figma may take a few seconds for large frames; image URLs expire (~30 days).
- **Comments accept lightweight markdown** in the `message` field, but no rich formatting beyond newlines.
- **The Plugin API ≠ the REST API.** Anything you find that says "create rectangle / set fill" is the Plugin API (TypeScript inside Figma). You can't call it from outside Figma.
- **FigJam files use the same endpoints** but the node shapes are different (`STICKY`, `SHAPE_WITH_TEXT`, `CONNECTOR`).

## Document shape (skeleton)

```json
{
  "document": {
    "id": "0:0",
    "name": "Document",
    "type": "DOCUMENT",
    "children": [
      {
        "id": "0:1",
        "name": "Page 1",
        "type": "CANVAS",
        "children": [
          {
            "id": "1:2",
            "name": "Architecture",
            "type": "FRAME",
            "children": [...]
          }
        ]
      }
    ]
  },
  "components": {...},
  "styles": {...},
  "name": "My file",
  "lastModified": "2026-05-20T...",
  "version": "..."
}
```

Most interesting node types: `FRAME`, `GROUP`, `COMPONENT`, `INSTANCE`, `RECTANGLE`, `TEXT`, `CONNECTOR` (FigJam), `STICKY` (FigJam).
