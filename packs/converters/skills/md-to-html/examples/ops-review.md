# Example: a quarterly ops review as one HTML file

**What the user said:** *"Turn `ops-review.md` into something the operations committee can
open from an email and print. Add a contents box."*

The input is [`inputs/ops-review.md`](inputs/ops-review.md). It has nested and task lists, a
quote, an aligned table, a local SVG chart ([`inputs/chart.svg`](inputs/chart.svg)), a Mermaid
fence, a Python code block, and two things that should not survive as-is: an inline
`<script>` and a pasted `<div>` block. (A `javascript:` link would also be dropped, with a
warning naming it.)

## Command

```bash
python3 scripts/md_to_html.py examples/inputs/ops-review.md -o ops-review.html --toc
```

## What the script printed (real output)

```text
warning: 1 Mermaid diagram(s) kept as text; use --mermaid cdn to draw them (needs network when opened), or render them to SVG with mermaid-render
warning: raw HTML found and shown as text (2 place(s)); this is deliberate, see --allow-html
wrote ops-review.html (6 KB): 5 headings, 1 tables, 1 code blocks, 1 Mermaid, 1 images embedded, 0 remote, 0 missing
```

## The `<main>` of the output (real, base64 shortened)

```html
<h1 id="northwind-health-q3-platform-review">Northwind Health: Q3 platform review<a class="anchor" href="#northwind-health-q3-platform-review" aria-hidden="true">#</a></h1>
<nav class="toc" aria-label="Contents"><p>Contents</p><ul><li><a href="#summary">Summary</a></li><li><a href="#numbers">Numbers</a></li><li><a href="#how-a-reminder-is-sent">How a reminder is sent</a></li><li><a href="#notes">Notes</a></li></ul></nav>
<p>Prepared for the <strong>operations committee</strong>. Figures are <em>placeholders</em> for this example.</p>
<h2 id="summary">Summary<a class="anchor" href="#summary" aria-hidden="true">#</a></h2>
<ul>
<li>Uptime held at the target for the quarter</li>
<li>Two incidents, both under 30 minutes
<ul>
<li>INC-101: login latency</li>
<li>INC-102: delayed reminder emails</li>
</ul></li>
<li class="task"><input type="checkbox" disabled checked> Migrate reminders to the new queue</li>
<li class="task"><input type="checkbox" disabled> Retire the old scheduler</li>
</ul>
<blockquote><p>Decision needed: approve the scheduler retirement for October.</p></blockquote>
<h2 id="numbers">Numbers<a class="anchor" href="#numbers" aria-hidden="true">#</a></h2>
<div class="table-wrap"><table><thead><tr><th style="text-align:left">Metric</th><th style="text-align:right">Q2</th><th style="text-align:right">Q3</th><th style="text-align:center">Change</th></tr></thead><tbody><tr><td style="text-align:left">Uptime</td><td style="text-align:right">99.90%</td><td style="text-align:right">99.95%</td><td style="text-align:center">up</td></tr><tr><td style="text-align:left">Incidents</td><td style="text-align:right">4</td><td style="text-align:right">2</td><td style="text-align:center">down</td></tr><tr><td style="text-align:left"><code>p95</code> login (ms)</td><td style="text-align:right">410</td><td style="text-align:right">380</td><td style="text-align:center">down</td></tr></tbody></table></div>
<p><img src="data:image/svg+xml;base64,…" alt="Weekly active members"></p>
<h2 id="how-a-reminder-is-sent">How a reminder is sent<a class="anchor" href="#how-a-reminder-is-sent" aria-hidden="true">#</a></h2>
<pre class="mermaid">flowchart LR
    Sched([Scheduler]) --&gt;|enqueue| Q{{Reminder queue}}
    Q --&gt; W[Worker]
    W --&gt;|SMTP| Mail[(Mail relay)]</pre>
<p>The worker retries with this rule:</p>
<pre><code class="language-python">def backoff(attempt):
    return min(2 ** attempt, 300)  # seconds, capped at 5 minutes</code></pre>
<h2 id="notes">Notes<a class="anchor" href="#notes" aria-hidden="true">#</a></h2>
<p>Raw HTML is shown as text, not run: &lt;script&gt;alert(&quot;hi&quot;)&lt;/script&gt;</p>
<pre class="raw-html">&lt;div style=&quot;color:red&quot;&gt;This block came from a pasted email.&lt;/div&gt;</pre>
<p>See the <a href="https://northwindhealth.example/runbooks/reminders">runbook</a> for the retry rules.</p>
```

## With `--mermaid cdn`

The same command with `--mermaid cdn` adds exactly one script and a policy that allows only it
(real output):

```html
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src data: https:; style-src 'unsafe-inline'; font-src data: https:; script-src 'sha256-FFdGvPoYRnPQ2cUJFzJW6IyZn0u1kdvZbGgLe0Qjl8Y=' https://cdn.jsdelivr.net; connect-src https://cdn.jsdelivr.net">
<script type="module">import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.esm.min.mjs";mermaid.initialize({startOnLoad:true,securityLevel:"strict"});</script>
```

Opened in headless Chrome with network, the `<pre class="mermaid">` was replaced by a drawn
flowchart SVG.

## What to tell the user

> `ops-review.html` is ready: one 6 KB file with the chart embedded, so it works as an email
> attachment. Three things to know:
> - The reminder diagram shows as text. If the committee will be online, I can rebuild with
>   the diagram drawn (it then needs network when opened), or render it to an SVG and embed it.
> - The pasted `<div>` and `<script>` show as text on purpose. Delete them from the source if they
>   were not meant to be there.
>
> Print-preview it once: the table header repeats on each page and the runbook link prints its address.
