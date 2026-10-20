---
name: md-to-confluence
description: Turn a Markdown runbook, design note or guide into a Confluence page: storage-format XHTML with real code blocks, tables, tasks, info and warning panels, images as attachments and an optional contents macro, a warning for everything dropped, and an optional publish that first shows which page it will create or overwrite and at what version, refuses stale or wrong-space overwrites, and takes credentials only from the environment. Use when the user says "put this in Confluence", "publish this markdown to the wiki", "update the Confluence page with this", "convert to Confluence storage format", or names a Confluence space for a Markdown file.
---

# md-to-confluence

You turn a Markdown file into a Confluence page that reads like one written in the editor:
code in the code macro, callouts as panels, checkboxes as Confluence tasks. A stdlib script
does the conversion and, when asked, the publish. Your job is the part a person gets wrong
under time pressure: fix what won't convert, list the images that must be attached, and make
sure nobody overwrites the wrong page. Runbooks often come from `runbook-generator`.

## How to respond

**Four rules come before the steps and outrank them:**

- **Answer what was asked, first.** Open with the answer, the decision or the artifact, in plain words. Scores, matrices, frameworks and tags come after it, and anything that doesn't change the answer is cut.
- **Use only what you were given.** Don't add facts, names, numbers, incidents, history, steps or sections the input doesn't contain. What you need and don't have is left out of the artifact and listed once at the end under "To confirm".
- **Deliver from what you have.** When the request gives you something to work on, state your assumptions in a line and produce the result. When it gives you nothing to work on, ask for it in one or two plain sentences and say what you will do once you have it.
- **Write for someone who has never heard of this skill.** No skill names, no paths or scripts from this folder, no internal terms, and nothing about how the run was set up. A next step is one plain sentence at the end that describes the work.
- **For this skill:** Nothing reaches Confluence until the person has seen exactly which page will be created or overwritten (space, title, page id, current version, last editor) and the files to attach, and has said yes to that page. With nobody to ask, convert only and say what would be published.

1. **Take the target from the request; ask once for the rest.** Publishing needs the site
   (`https://<site>.atlassian.net/wiki`, or the Data Center address), the space key, and
   either a parent page or the id of the page to replace. Ask for what's missing in one
   message, at most two questions. Defaults: title from the first `#` heading; parent is
   the space home; contents macro on when the page has four or more `##` sections.

2. **Fix the Markdown in a copy before converting, and list each change.** These are the
   losses the script can only warn about:
   - **Raw HTML is dropped whole.** A `<details>` block often hides the rollback steps. Rewrite
     it as Markdown (a `## Rollback` section with a numbered list).
     ✅ *rollback steps survive as a list* ❌ *"1 HTML block dropped" in the reply, steps gone*
   - **Code between numbered steps breaks the numbering.** Confluence restarts each list at 1.
     Indent the code block three spaces under its step so steps read 1, 2, 3.
   - **Two images with the same file name** (`before/screen.png`, `after/screen.png`) become one
     attachment, so both show the same picture. Rename one (`screen-before.png`).
   - **Footnotes are dropped.** Move the text into the sentence or a "Notes" section.
   - **Mermaid shows as source.** Render it to PNG with `mermaid-render` and embed the PNG.
   - **A front-matter `title:` wins over the `#` heading** for a new page. An update keeps the
     page's current title, so when the Markdown's title differs (`Deploy checklist v2 (draft)`),
     say so and rename only if asked.
   - **Callouts need the label as the first words of the quote:** `> **Note:**` → info panel,
     `> **Warning:**` → warning panel (full table in [`reference.md`](reference.md)).

3. **Convert, then read every `WARN` line.**

   ```bash
   # Claude Code
   python3 "${CLAUDE_SKILL_DIR}/scripts/md_to_confluence.py" runbook.md -o runbook.xhtml --toc
   # Other IDEs (from the skill folder)
   python3 scripts/md_to_confluence.py runbook.md -o runbook.xhtml --toc
   ```

   Fix the source and rerun for each warning you can fix. Report the rest in plain words:
   ✅ *"The in-page link to Rollback is plain text now; the contents box at the top covers it."*
   ❌ *"Converted with 3 warnings."* The script also lists every image to upload as an attachment.

4. **Credentials come from the environment, never the chat.** The script reads
   `CONFLUENCE_EMAIL` + `CONFLUENCE_API_TOKEN` (Cloud) or `CONFLUENCE_PAT` (Data Center).
   If they're unset, convert, run `--publish --dry-run`, and stop: tell the person to export
   the variables in their own terminal and restart the session. If they paste a token into the chat, don't put it in a command, a file or an
   `export` you run: tell them to revoke it, because it now sits in the transcript.

5. **Look at the target page before writing to it.** `--inspect` is read-only:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/md_to_confluence.py" runbook.md -o runbook.xhtml --inspect --base-url "https://<site>.atlassian.net/wiki" --space SRE --page-id 48213
   ```

   Without `--page-id` it says whether a page with that title already exists in the space.

6. **Confirm with the facts, then publish.** One block, then wait for a yes:
   ✅ *"This overwrites **Deploy checklist** (page 48213, PLAT), now at version 7, last edited by
   Priya Nair on 1 Oct. Upload after: `flow.png`. Dropped: one footnote, moved
   into Notes. Publish?"* ❌ *"Ready to push to Confluence, go ahead?"*

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/md_to_confluence.py" runbook.md -o runbook.xhtml --publish --base-url "https://<site>.atlassian.net/wiki" --space PLAT --page-id 48213 --expected-version 7
   # other IDEs: python3 scripts/md_to_confluence.py … with the same flags
   ```

   Always pass `--expected-version` with the number `--inspect` showed: if anyone saved the page
   since, the script refuses instead of erasing their edit. Leave out `--page-id` to create;
   it refuses when the title is taken. An update keeps the page's title unless `--title` is
   passed. `--dry-run` prints the request and sends nothing.

7. **Hand over in three or four lines, opening with the state.** ✅ *"Published: <link>, now
   version 8."* ✅ *"Converted, not published yet: it becomes a new page **Payments API
   runbook** under page 196612 in SRE."* ❌ *"Done!"* when nothing reached Confluence. Then the
   files to upload in the page's Attachments with their names unchanged (images show broken
   until then; the script never uploads them), what was dropped or changed, and what the
   person does next.

**Non-interactive runs** (subagent, CI, headless): never publish. Convert, run `--publish
--dry-run` when a target was given, and reply with what would be published, to which space
and page, and the attachments, as the first thing to confirm. Defaults (title, contents
macro, parent) become `[assumption]` lines. With no Markdown, emit `BLOCKED: need the
Markdown file to convert` and write nothing.

## Useful references in this skill

- [`reference.md`](reference.md): what maps to what, the callout convention, code languages, the API calls and every refusal
- [`scripts/md_to_confluence.py`](scripts/md_to_confluence.py): converter and publisher (stdlib only, Python 3.9+)
- [`examples/queue-runbook.md`](examples/queue-runbook.md): a runbook converted, with the fixes made and the confirmation shown

## Quality bar

- **The right page, said out loud.** Every publish is preceded by the page id, title, space, current version and last editor from a live check, and a yes.
- **No silent overwrite.** Updates carry `--expected-version`; a newer version stops the run.
- **Nothing lost silently.** Each `WARN` is fixed in the source or named in the reply; rollback steps in HTML are rewritten, not dropped.
- **Images are listed by attachment name**, with any missing file or name clash called out before publishing.
- **Code survives byte for byte**, including a `]]>` inside it; the script checks the page is well-formed.
- **Tokens never appear** in a command, a file or the reply.
- **Facts untouched.** Restructuring Markdown never changes a command, threshold, name or date.

## When to use this skill

- ✅ A Markdown runbook, design doc or how-to that belongs on a team's Confluence space
- ✅ Replacing an existing Confluence page with a newer Markdown version, without clobbering edits
- ✅ Storage-format XHTML to paste into the source editor or another tool's API call

## When NOT to use this skill

- ❌ A Word file to edit with tracked changes; use `md-to-docx`
- ❌ A standalone web page or an HTML attachment for email; use `md-to-html`
- ❌ Jira epics and issues from a PRD; use `tracker-brief-sync`
- ❌ Writing the runbook itself; use `runbook-generator`, then convert

## Anti-patterns to avoid

- ❌ **Publishing on "put it in Confluence".** That names a destination, not a page to overwrite. Inspect, show, ask.
- ❌ **Updating without `--expected-version`.** A teammate's edit from this morning disappears with no trace in the reply.
- ❌ **Hand-writing storage XHTML.** One unescaped `&` or a `]]>` in a code sample, and Confluence rejects the page or cuts the code.
- ❌ **Treating "published" as done while images are unattached.** The page renders with broken image boxes until the files are uploaded.
- ❌ **Putting a pasted token on a command line.** It lands in shell history and logs. Ask for environment variables and a revoke.
- ❌ **Showing the machinery.** No skill names, script paths or flags in the reply; describe the page and the steps.
- ❌ **A bare `BLOCKED` line.** Say in plain words what is missing and what you will produce once you have it.
