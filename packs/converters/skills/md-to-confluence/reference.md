# md-to-confluence reference

## What converts to what

| Markdown | Confluence storage format |
|---|---|
| `#` to `######`, setext `===` / `---` | `<h1>` to `<h6>`. The first `#` heading becomes the page title and leaves the body (Confluence prints the title above the page); `--keep-h1` keeps it |
| `**bold**`, `*italic*`, `~~strike~~`, `` `code` `` | `<strong>`, `<em>`, line-through span, `<code>` |
| Inline, reference-style and bare links | `<a href>`. `javascript:`, `data:`, `file:` targets are dropped (text kept). `#anchor` links become plain text: Confluence names heading anchors after the page title, so a Markdown slug never matches |
| `-` and `1.` lists, nested | `<ul>` / `<ol>`. A list that starts at 2 or later restarts at 1, with a warning |
| A list made only of `- [ ]` / `- [x]` items | `<ac:task-list>`, one `<ac:task>` per item, complete or incomplete. Mixed with plain items: written as ☐ / ☑ text, with a warning |
| Pipe table | `<table>`, first row as `<th>`; `:---:` / `---:` alignment kept as a paragraph style in each cell |
| `> quote` | `<blockquote>` |
| Callout (below) | info, tip, note or warning macro, label removed (the panel's icon says it) |
| Fenced or indented code | `code` macro, body in CDATA. `]]>` inside the code is split as `]]]]><![CDATA[>`, so it reads back byte for byte |
| An image with a local path, `img/x.png` | `<ac:image><ri:attachment ri:filename="x.png"/></ac:image>`, matched by file name only |
| An image with an `https://` address | `<ac:image><ri:url/></ac:image>`, with a warning: it breaks if that site moves or needs a login |
| `---` | `<hr />` |
| `--toc` | `toc` macro at the top |
| **Dropped, with a WARN line** | raw HTML blocks (whole), inline HTML tags (text kept; `<br>` kept), footnotes, `data:` images, YAML front matter (its `title:` is used as the page title) |

Text is escaped once, after `&amp;`-style references are decoded, so nothing in the Markdown
can open a macro or a tag in the page. Before writing, the script parses its own output as XML
and stops if it is malformed.

## Callout convention

The label is bold, ends in a colon, and opens the quote. GitHub's `> [!NOTE]` form works too.

| Write | Panel |
|---|---|
| `> **Note:**` or `> **Info:**` or `> [!NOTE]` | info (blue) |
| `> **Tip:**` or `> [!TIP]` | tip (green) |
| `> **Important:**` or `> [!IMPORTANT]` | note (yellow) |
| `> **Warning:**`, `> **Caution:**`, `> [!WARNING]`, `> [!CAUTION]` | warning (red) |

✅ `> **Warning:** Never restart all three replicas at once.` ❌ `> Warning - never restart…`
(a plain quote: no panel).

## Code languages

Highlighted on Cloud and Data Center: bash, c#, cpp, css, diff, go, groovy, java, js, json,
kotlin, perl, php, powershell, py, ruby, sass, scala, sql, text, typescript, vb, xml, yml, and a
few older ones. Aliases map automatically (`python` → py, `sh`/`shell`/`zsh` → bash, `yaml` →
yml, `html` → xml, `ts` → typescript). Any other language is shown without highlighting, with a
warning. A `mermaid` fence stays a code block.

## Publishing

All calls go to the v1 content API at `<base>/rest/api/content`, which Cloud and Data Center
both serve. For a Cloud host the script adds `/wiki` if the base URL lacks it.

| Mode | Calls | Writes to Confluence |
|---|---|---|
| `--inspect --page-id N` | GET page N with version and space | no |
| `--inspect` (no page id) | GET pages in the space with this title | no |
| `--publish --dry-run` | none | no |
| `--publish` (create) | GET by title, then POST | yes, a new page |
| `--publish --page-id N` | GET page N, then PUT with version + 1 | yes, a new version |

**Refusals** (exit 2, nothing written): a base URL that isn't `https`, or carries a user name
or password; no credentials in the environment; a page in another space than `--space`; a page
not at `--expected-version`; a create whose title already exists in the space. A redirect is
never followed, so the credentials go to the host you named and nowhere else. HTTP errors exit 1
with the status and Confluence's message (401 credentials, 403 permission, 404 missing or hidden,
409 someone saved meanwhile).

## Credentials

Read from the environment only, never from arguments or files, and never printed.

| Variable | Used for |
|---|---|
| `CONFLUENCE_EMAIL` + `CONFLUENCE_API_TOKEN` | Cloud: basic auth. Token from id.atlassian.com, Security, API tokens |
| `CONFLUENCE_PAT` | Data Center: bearer token. From your profile, Personal Access Tokens |

When both are set, a `*.atlassian.net` host uses the email and API token; any other host uses the PAT.

```bash
export CONFLUENCE_EMAIL="<your Atlassian account email>"
export CONFLUENCE_API_TOKEN="<token from id.atlassian.com>"
```

Run those in your own terminal before starting the agent, or pull them from a secret manager.
A Data Center host is not `*.atlassian.net`: add it to the sandbox's allowed hosts yourself if
the project is contained.

## Attachments

The script never uploads files. After the page exists, upload each listed file to the page
(page menu, Attachments) with its name unchanged; the `ri:filename` in the page is matched
exactly, case included. Until then Confluence shows a broken image box.
