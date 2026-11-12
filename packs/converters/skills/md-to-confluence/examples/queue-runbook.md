# Example: a short runbook onto a Confluence space

**What the user said:** *"Put `queue-runbook.md` in Confluence under the Runbooks page
(196612) in the OPS space on northwind.atlassian.net."*

The input is [`inputs/queue-runbook.md`](inputs/queue-runbook.md). It has a warning callout, an
image, a numbered list split by an unindented code block, and the scale-down step hidden in a
`<details>` HTML block.

## First conversion (real output)

```text
WARN line 17: numbered list starts at 2 but Confluence restarts it at 1; indent the code block or text that split the list under the previous item so it stays one list
WARN line 19: raw HTML block dropped (lines 19-21); rewrite it as Markdown to keep it
wrote queue-runbook.xhtml (1 KB storage format): title "Order queue runbook"; 2 headings, 0 tables, 1 code blocks, 1 callouts, 0 task lists, 1 images to attach, 0 remote images
upload these files to the page as attachments, with exactly these names, or the images show as broken:
  queue-depth.png  (from img/queue-depth.png)
```

Both warnings are fixable in the source, so neither goes to the user as a loss. The fixed copy
is [`inputs/queue-runbook.fixed.md`](inputs/queue-runbook.fixed.md): the code block is indented
three spaces under step 1, and the `<details>` block became a `## Scale back down` section with
its sentence unchanged. The rerun prints no warnings.

## The page body after the fix (real, abridged)

```xml
<ac:structured-macro ac:name="warning" ac:schema-version="1"><ac:rich-text-body><p>Purging the queue deletes orders. Never purge without the fulfilment lead.</p></ac:rich-text-body></ac:structured-macro>
<h2>Check the backlog</h2><p><ac:image ac:alt="Queue depth panel"><ri:attachment ri:filename="queue-depth.png" /></ac:image></p>
<ol><li><p>Read the depth:</p><ac:structured-macro ac:name="code" ac:schema-version="1"><ac:parameter ac:name="language">bash</ac:parameter><ac:plain-text-body><![CDATA[qctl depth orders-in]]></ac:plain-text-body></ac:structured-macro></li>
<li><p>If it is above 2,000 for 10 minutes, scale the workers to 6.</p></li></ol>
<h2>Scale back down</h2><p>Once depth is under 200, scale the workers back to 3.</p>
```

## The dry run (real output; no credentials were set)

```text
dry run: nothing was sent
  POST https://northwind.atlassian.net/wiki/rest/api/content
  space OPS, title "Order queue runbook", parent 196612
  body: 847 bytes of storage format
  first checks space OPS for a page with this title and stops if one exists
  auth: none found: set CONFLUENCE_EMAIL and CONFLUENCE_API_TOKEN (Cloud) or CONFLUENCE_PAT (Data Center) in the environment
```

## The reply

> The runbook is converted and ready to go up as a new page, **Order queue runbook**, under
> page 196612 in the OPS space. Nothing has been published yet.
>
> - **Two fixes to the source:** the `qctl depth` command now sits inside step 1, so the steps
>   stay numbered 1 and 2; the hidden "Scale back down" block is now its own section, so it
>   isn't dropped.
> - **One file to attach after publishing:** `queue-depth.png`, name unchanged, or the panel shows as a broken image.
> - **Before I can publish:** set `CONFLUENCE_EMAIL` and `CONFLUENCE_API_TOKEN` in your terminal
>   and restart the session. I'll then check that no OPS page already has this title, show you
>   the result, and publish once you say yes.
