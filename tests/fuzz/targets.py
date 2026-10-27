"""Fuzz targets: the skill scripts that parse files a user hands them (RFC-0062).

Each target runs one script the way a user does, with the fuzzed bytes written to the file it
reads, and passes when the script either succeeds or rejects the input the way it promises:
an exit code from `ok_exits`, or argparse's own error. Any other exception is a crash: the
traceback a user would see instead of a message.

The seeds are small, valid inputs. The fuzzer mutates them. The Office and Outlook seeds are
built in code (tests/fuzz/seeds.py), since a fuzzer can't reach a binary parser from a file that
fails its first header check.

An optional eighth field holds two extras:
- "wrap": a function that builds the file from the fuzzed bytes. The read-*-xml targets fuzz the
  XML part of an Office file inside a valid package, since a mutated zip mostly fails its checksum
  before any XML is read.
- "then": further steps that read what the first one wrote. For md-to-docx, md-to-xlsx and
  md-to-pptx the next step is file-to-markdown, so every file one converter writes must be one the
  other reads. A later step must succeed outright: if the writer accepted the input, the reader
  rejecting its file is a finding too.
"""
import contextlib
import inspect
import io
import os
import sys
import tempfile

from tests.fuzz import seeds
from tests.support import load

# (name, skill, script, argv with {in}, {out} and {root}, input suffix, exit codes that mean "handled", seeds
#  [, {"wrap": bytes -> file bytes, "then": [(skill, script, argv), ...]}])
# A suffix starting with "/" places the input inside a throwaway repository at that path, with a
# sibling record and the folder it names, and {root} is that repository.
# A Markdown file using most of what the converters handle, for the ones that read Markdown.
MARKDOWN = (
    b"---\ntitle: Release notes\n---\n# Release notes\n\nIntro with **bold**, *italic*, ~~gone~~, `code` and a "
    b"[link](https://docs.example/a?b=1&c=2).[^1]\n\n## Fixed\n\n1. The importer\n   - nested *item*\n2. Exports\n\n"
    b"- [x] done\n- [ ] open\n\n| Area | Count | Note |\n|:--|--:|:-:|\n| Billing | 3 | a \\| b |\n| Search | 10 | |\n\n"
    b"> **Note**\n> quoted line\n\n```python\nprint('x')\n```\n\n---\n\n![chart](chart.png)\n\n"
    b"Line one  \nline two<br>three &amp; four\n\n[^1]: A footnote.\n"
)

TARGETS = [
    ("sql", "sql-review", "sql_lint.py", ["{in}", "--format", "json", "-o", "{out}"], ".sql", (0, 1, 2), [
        b"select a.id, count(*) / count(b.x) as r from a left join b on a.id = b.a_id\n"
        b"where b.status = 'paid' group by 1 having count(*) > 1;\n",
        b"SELECT DISTINCT o.id, SUM(i.qty) FROM orders o JOIN items i USING (order_id) GROUP BY o.id;",
    ]),
    ("lighthouse", "web-performance-review", "lh_summary.py", ["{in}", "--json", "-o", "{out}"], ".json", (0, 1, 2), [
        b'{"lighthouseVersion":"12.0.0","requestedUrl":"https://shop.example/","finalUrl":"https://shop.example/",'
        b'"configSettings":{"formFactor":"mobile","throttlingMethod":"simulate"},'
        b'"categories":{"performance":{"score":0.82}},"audits":{"largest-contentful-paint":{"numericValue":3100,'
        b'"displayValue":"3.1 s","score":0.6},"cumulative-layout-shift":{"numericValue":0.12,"score":0.7}}}',
        b'{"loadingExperience":{"metrics":{"LARGEST_CONTENTFUL_PAINT_MS":{"percentile":4300}}},'
        b'"lighthouseResult":{"lighthouseVersion":"12.0.0","audits":{}}}',
    ]),
    ("terraform-plan", "terraform-plan-review", "plan_summary.py", ["{in}", "--format", "json", "-o", "{out}"], ".json", (0, 1, 2), [
        b'{"format_version":"1.2","resource_changes":[{"address":"aws_s3_bucket.logs","type":"aws_s3_bucket",'
        b'"change":{"actions":["delete","create"],"before":{"acl":"private"},"after":{"acl":"public-read"}}},'
        b'{"address":"aws_security_group_rule.ssh","type":"aws_security_group_rule","change":{"actions":["create"],'
        b'"before":null,"after":{"cidr_blocks":["0.0.0.0/0"],"from_port":22,"to_port":22}}}]}',
    ]),
    ("brand", "brand-kit", "check_brand.py", ["{in}"], ".json", (0, 1, 2), [
        b'{"name":"Fernvale Trust","colors":{"primary":"#1a4d2e","text":"#111111","background":"#ffffff",'
        b'"accent":"#f2a541"},"fonts":{"heading":"Georgia","body":"Arial"},"logo":{"path":"logo.svg","alt":"Fernvale"}}',
    ]),
    ("cloud-cost", "cloud-cost-review", "cost_summary.py", ["{in}", "--format", "auto"], ".csv", (0, 1, 2), [
        b"lineItem/UsageAccountId,lineItem/ProductCode,lineItem/UsageType,lineItem/UnblendedCost,lineItem/UsageStartDate\n"
        b"111111111111,AmazonEC2,USE1-BoxUsage:m5.large,12.50,2026-08-01T00:00:00Z\n"
        b"111111111111,AmazonEC2,USE1-SpotUsage:m5.large,3.10,2026-08-01T00:00:00Z\n"
        b"111111111111,AmazonS3,USE1-TimedStorage-ByteHrs,0.75,2026-08-02T00:00:00Z\n",
    ]),
    ("backlog", "backlog-triage", "triage_backlog.py", ["{in}", "--as-of", "2026-10-01", "-o", "{out}"], ".csv", (0, 1, 2), [
        b"Issue key,Summary,Status,Priority,Assignee,Created,Updated,Description\n"
        b"CHK-1,Guest checkout,To Do,High,,2026-01-05,2026-02-01,\n"
        b"CHK-2,Guest check out,In Progress,Medium,Ana,2026-06-01,2026-09-30,As a guest I can pay\n",
    ]),
    ("status", "team-status-report", "status_counts.py", ["{in}", "--from", "2026-09-01", "--to", "2026-09-14", "-o", "{out}"], ".csv", (0, 1, 2), [
        b"Issue key,Summary,Status,Issue Type,Sprint,Resolved,Created,Flagged\n"
        b"CHK-1,Pay,Done,Story,CHK Sprint 1,2026-09-03,2026-08-20,\n"
        b"CHK-2,Email,Blocked,Story,CHK Sprint 14,,2026-08-25,Impediment\n",
    ]),
    ("risk-register", "risk-register", "check_register.py", ["{in}", "--as-of", "2026-10-01", "--out", "{out}"], ".csv", (0, 1, 2), [
        b"id,title,owner,likelihood,impact,inherent,treatment,controls,residual,due_date,next_review,status\n"
        b"R-001,Supplier outage,Ops Lead,3,4,12,reduce,Second supplier,6,2026-11-30,2026-12-01,open\n"
        b"R-002,Data loss,IT Lead,2,5,10,accept,,10,,2026-09-15,open\n",
    ]),
    ("golden-diff", "behaviour-equivalence", "golden_diff.py", ["{in}", "{in}", "--rules", "{in}"], ".jsonl", (0, 1, 2), [
        b'{"case":"a","output":{"total":10.0,"at":"2026-10-01T10:00:00Z"}}\n{"case":"b","output":{"total":3}}\n',
        b'{"ignore":["at"],"round":{"total":2}}',
    ]),
    ("asyncapi", "event-contract-draft", "check_asyncapi.py", ["{in}", "-o", "{out}"], ".json", (0, 1, 2), [
        b'{"asyncapi":"3.0.0","info":{"title":"Orders","version":"1.0.0"},"channels":{"orders":{"address":"orders.v1",'
        b'"messages":{"OrderPlaced":{"payload":{"type":"object","properties":{"id":{"type":"string"}}}}}}},'
        b'"operations":{"publish":{"action":"send","channel":{"$ref":"#/channels/orders"}}}}',
    ]),
    ("bundle-stats", "bundle-size-review", "bundle_stats.py", ["{in}", "--json", "-o", "{out}"], ".json", (0, 1, 2), [
        b'{"version":"5.94.0","assets":[{"name":"main.js","size":120000,"chunks":[0]}],"chunks":[{"id":0,'
        b'"initial":true,"names":["main"],"files":["main.js"],"modules":[{"name":"./node_modules/lodash/lodash.js",'
        b'"size":544098}]}],"entrypoints":{"main":{"assets":[{"name":"main.js"}]}}}',
    ]),
    ("feedback-themes", "feedback-synthesis", "theme_counts.py", ["{in}", "-o", "{out}"], ".csv", (0, 1, 2), [
        b"id,person,segment,theme,quote\n1,P1,SMB,pricing,Too dear for us\n2,P2,Enterprise,pricing,Fine\n3,P1,SMB,onboarding,Lost\n",
    ]),
    ("citations", "source-synthesis", "citations.py", ["{in}", "-o", "{out}"], ".md", (0, 1, 2), [
        b"# Findings\n\nRetention fell by a third [S1:p4]. Two teams disagree [S2:p7][S3].\n\n## Sources\n\n"
        b"- S1: Survey 2026\n- S2: Interviews\n- S3: Tickets\n",
    ]),
    ("ach-matrix", "hypothesis-comparison", "ach_matrix.py", ["{in}", "-o", "{out}"], ".csv", (0, 1, 2), [
        b"evidence,credibility,H1 tracking bug,H2 real drop\nE1 drop only on Safari,high,C,I\nE2 support tickets flat,medium,C,I\n",
    ]),
    ("context-graph", "context-graph", "context_graph.py", ["--root", "{root}", "--json", "-o", "{out}"],
     "/docs/adr/0003-order-events.md", (0, 1, 2), [
        b"---\nstatus: accepted\ndate: 2026-02-10\n---\n# Order events on SQS\n\nSupersedes ADR-0002. Published from "
        b"`services/orders/`, see [ADR 1](0001-record.md) and RFC-0012.\n",
        b"# ADR 3: Kafka\n\n## Status\n\nSuperseded by ADR-0009\n\nDate: 2025-01-02\n\nAmends ADR-0001. `src/x/*`\n",
    ]),
    ("md-to-confluence", "md-to-confluence", "md_to_confluence.py", ["{in}", "-o", "{out}.xhtml", "--toc"], ".md", (0, 1, 2), [MARKDOWN]),
    # file-to-markdown's readers, each from a valid file of its kind
    ("read-msg", "file-to-markdown", "to_markdown.py", ["{in}", "-o", "{out}.md"], ".msg", (0, 1, 2), [seeds.outlook_msg()]),
    ("read-eml", "file-to-markdown", "to_markdown.py", ["{in}", "-o", "{out}.md"], ".eml", (0, 1, 2), [
        b"From: Avery Example <avery@example.com>\r\nTo: robin@example.com\r\nSubject: =?utf-8?q?Quarterly_figures?=\r\n"
        b"Date: Sat, 18 Jun 2022 04:26:00 +0000\r\nMIME-Version: 1.0\r\nContent-Type: multipart/mixed; boundary=\"b1\"\r\n\r\n"
        b"--b1\r\nContent-Type: text/html; charset=utf-8\r\n\r\n<p>Hello, the <b>figures</b> are attached.</p>\r\n"
        b"--b1\r\nContent-Type: text/csv; name=\"figures.csv\"\r\nContent-Disposition: attachment; filename=\"figures.csv\"\r\n"
        b"Content-Transfer-Encoding: base64\r\n\r\ncmVnaW9uLHRvdGFsCm5vcnRoLDEyCg==\r\n--b1--\r\n",
    ]),
    ("read-docx", "file-to-markdown", "to_markdown.py", ["{in}", "-o", "{out}.md"], ".docx", (0, 1, 2), [seeds.docx()]),
    ("read-xlsx", "file-to-markdown", "to_markdown.py", ["{in}", "-o", "{out}.md"], ".xlsx", (0, 1, 2), [seeds.xlsx()]),
    ("read-pptx", "file-to-markdown", "to_markdown.py", ["{in}", "-o", "{out}.md"], ".pptx", (0, 1, 2), [seeds.pptx()]),
    ("read-docx-xml", "file-to-markdown", "to_markdown.py", ["{in}", "-o", "{out}.md"], ".docx", (0, 1, 2),
     [seeds.DOCX_XML.encode()], {"wrap": seeds.docx}),
    ("read-xlsx-xml", "file-to-markdown", "to_markdown.py", ["{in}", "-o", "{out}.md"], ".xlsx", (0, 1, 2),
     [seeds.XLSX_XML.encode()], {"wrap": seeds.xlsx}),
    ("read-pptx-xml", "file-to-markdown", "to_markdown.py", ["{in}", "-o", "{out}.md"], ".pptx", (0, 1, 2),
     [seeds.PPTX_XML.encode()], {"wrap": seeds.pptx}),
    # round-trips: Markdown to an Office file, then back with file-to-markdown
    ("roundtrip-docx", "md-to-docx", "md_to_docx.py", ["{in}", "-o", "{out}.docx"], ".md", (0, 1, 2), [MARKDOWN],
     {"then": [("file-to-markdown", "to_markdown.py", ["{out}.docx", "-o", "{out}.back.md"])]}),
    ("roundtrip-xlsx", "md-to-xlsx", "md_to_xlsx.py", ["{in}", "-o", "{out}.xlsx", "--formulas"], ".md", (0, 1, 2), [
        b"# Totals\n\n| Region | Q1 | Q2 | Total |\n|---|--:|--:|---|\n| North | 1,200 | 3.5% | =B2+C2 |\n"
        b"| South | (40) | 2026-01-31 | `x` |\n\n## Notes\n\n| a |\n|---|\n| TRUE |\n",
    ], {"then": [("file-to-markdown", "to_markdown.py", ["{out}.xlsx", "-o", "{out}.back.md"])]}),
    ("roundtrip-pptx", "md-to-pptx", "md_to_pptx.py", ["{in}", "-o", "{out}.pptx"], ".md", (0, 1, 2), [MARKDOWN],
     {"then": [("file-to-markdown", "to_markdown.py", ["{out}.pptx", "-o", "{out}.back.md"])]}),
]

BY_NAME = {t[0]: t for t in TARGETS}


class Crash(Exception):
    """The script raised something other than a clean exit: what a user would see as a traceback."""


def runner(name):
    """A function taking the fuzzed bytes, running the target once, raising Crash on a crash."""
    _, skill, script, argv, suffix, ok, _ = BY_NAME[name][:7]
    extras = BY_NAME[name][7] if len(BY_NAME[name]) > 7 else {}
    wrap = extras.get("wrap")
    steps = [(load(skill, script), script, argv)]
    steps += [(load(s, sc), sc, av) for s, sc, av in extras.get("then", ())]
    work = tempfile.mkdtemp(prefix="skilldrop-fuzz-")
    out, repo = os.path.join(work, "out"), os.path.join(work, "repo")
    if suffix.startswith("/"):
        src = os.path.join(repo, *suffix.strip("/").split("/"))
        os.makedirs(os.path.dirname(src), exist_ok=True)
        os.makedirs(os.path.join(repo, "services", "orders"), exist_ok=True)
        with open(os.path.join(os.path.dirname(src), "0001-record.md"), "w", encoding="utf-8") as fh:
            fh.write("# ADR-0001: Record decisions\n\nStatus: Accepted\n")
    else:
        src = os.path.join(work, "input" + suffix)

    def call(mod, script, argv):
        args = [a.replace("{in}", src).replace("{out}", out).replace("{root}", repo) for a in argv]
        if isinstance(getattr(mod, "WARNINGS", None), list):
            del mod.WARNINGS[:]  # module-level warnings would otherwise pile up across inputs
        saved, err = sys.argv, io.StringIO()
        sys.argv = [script] + args
        try:
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
                code = mod.main(args) if inspect.signature(mod.main).parameters else mod.main()
        except SystemExit as e:
            code = e.code
        except Exception as e:  # noqa: BLE001  (any other exception is the finding)
            raise Crash("%s: %s: %s: %s" % (name, script, type(e).__name__, e)) from e
        finally:
            sys.argv = saved
        return code, err.getvalue()

    def one(data):
        for path in os.listdir(work):  # a previous input's outputs must not feed this one's later steps
            if path.startswith("out"):
                os.remove(os.path.join(work, path))
        with open(src, "wb") as fh:
            fh.write(wrap(data) if wrap else data)
        mod, script, argv = steps[0]
        code, _ = call(mod, script, argv)
        if not (isinstance(code, str) or code is None or code in ok):  # sys.exit("message") or a plain return is fine
            raise Crash("%s: exit code %r is not one the script documents (%s)" % (name, code, ok))
        if code not in (0, None):
            return  # the first step rejected the input cleanly; there is nothing to read back
        for mod, script, argv in steps[1:]:
            code, err = call(mod, script, argv)
            if code not in (0, None):
                raise Crash("%s: %s could not read what the step before it wrote (exit %r): %s"
                            % (name, script, code, (code if isinstance(code, str) else err.strip())[-300:]))
    return one
