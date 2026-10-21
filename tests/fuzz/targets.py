"""Fuzz targets: the skill scripts that parse files a user hands them (RFC-0062).

Each target runs one script the way a user does, with the fuzzed bytes written to the file it
reads, and passes when the script either succeeds or rejects the input the way it promises:
an exit code from `ok_exits`, or argparse's own error. Any other exception is a crash: the
traceback a user would see instead of a message.

The seeds are small, valid inputs. The fuzzer mutates them.
"""
import contextlib
import inspect
import io
import os
import sys
import tempfile

from tests.support import load

# (name, skill, script, argv with {in} and {out}, input suffix, exit codes that mean "handled", seeds)
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
    ("md-to-html", "md-to-html", "md_to_html.py", ["{in}", "-o", "{out}", "--toc"], ".md", (0, 1, 2), [
        b"### Note\n\n## Setup\n\nRun **this** `cmd` and see [docs](https://docs.example/).\n\n| a | b |\n|---|---|\n| 1 | 2 |\n"
        b"\n```python\nprint('x')\n```\n\n- [ ] task\n> quote\n",
    ]),
]

BY_NAME = {t[0]: t for t in TARGETS}


class Crash(Exception):
    """The script raised something other than a clean exit: what a user would see as a traceback."""


def runner(name):
    """A function taking the fuzzed bytes, running the target once, raising Crash on a crash."""
    _, skill, script, argv, suffix, ok, _ = BY_NAME[name]
    mod = load(skill, script)
    takes_argv = bool(inspect.signature(mod.main).parameters)
    work = tempfile.mkdtemp(prefix="skilldrop-fuzz-")
    src, out = os.path.join(work, "input" + suffix), os.path.join(work, "out")

    def one(data):
        with open(src, "wb") as fh:
            fh.write(data)
        args = [a.replace("{in}", src).replace("{out}", out) for a in argv]
        saved = sys.argv
        sys.argv = [script] + args
        try:
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                code = mod.main(args) if takes_argv else mod.main()
        except SystemExit as e:
            code = e.code
        except Exception as e:  # noqa: BLE001  (any other exception is the finding)
            raise Crash("%s: %s: %s" % (name, type(e).__name__, e)) from e
        finally:
            sys.argv = saved
        if isinstance(code, str) or code is None:  # sys.exit("message") or a plain return
            return
        if code not in ok:
            raise Crash("%s: exit code %r is not one the script documents (%s)" % (name, code, ok))
    return one
