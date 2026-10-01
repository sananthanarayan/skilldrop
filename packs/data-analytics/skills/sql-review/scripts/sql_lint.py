#!/usr/bin/env python3
"""Flag the mechanical SQL smells that most often produce wrong numbers.

This is the first pass of a SQL review, not the review. It reads text with
regular expressions; it does not parse SQL or know your schema, so every
finding is a place to look, not a verdict. The correctness review (join
fan-out, grain, timezone boundaries) still has to be done by reading the
query.

Usage:
    python3 sql_lint.py query.sql --dialect postgres
    python3 sql_lint.py query.sql --dialect bigquery --format json -o findings.json
    cat query.sql | python3 sql_lint.py - --dialect snowflake --strict

Exit codes: 0 = ran (findings or not); 1 = --strict and at least one
error/warn finding; 2 = bad input (missing file, empty, not SQL).
Stdlib only. Runs on Python 3.9+.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from typing import List, Optional, Tuple

DIALECTS = ("generic", "postgres", "bigquery", "snowflake", "redshift", "mysql", "sqlserver")
# Dialects where INT / INT truncates to an integer.
INT_DIVISION_DIALECTS = {"generic", "postgres", "redshift", "sqlserver"}
SEVERITY_ORDER = {"error": 0, "warn": 1, "info": 2}

CLAUSE_END = re.compile(
    r"\b(group\s+by|order\s+by|limit|having|qualify|union|window|intersect|except)\b"
)
TS_COL = re.compile(r"(_at|_ts|_time|timestamp|datetime|_dttm)$", re.I)
DATE_COL = re.compile(r"(date|_dt|_day)$", re.I)


def mask(sql: str) -> Tuple[str, str]:
    """Return (no_comments, masked).

    no_comments: comments replaced by spaces; string literals kept.
    masked: comments and string-literal interiors replaced, so keywords
    inside strings never match. Both keep every newline and offset.
    """
    out_nc = []
    out_m = []
    i = 0
    n = len(sql)
    while i < n:
        c = sql[i]
        nxt = sql[i + 1] if i + 1 < n else ""
        if c == "-" and nxt == "-":
            j = sql.find("\n", i)
            j = n if j == -1 else j
            blank = " " * (j - i)
            out_nc.append(blank)
            out_m.append(blank)
            i = j
        elif c == "/" and nxt == "*":
            j = sql.find("*/", i + 2)
            j = n if j == -1 else j + 2
            blank = "".join("\n" if ch == "\n" else " " for ch in sql[i:j])
            out_nc.append(blank)
            out_m.append(blank)
            i = j
        elif c == "'":
            j = i + 1
            while j < n:
                if sql[j] == "'" and j + 1 < n and sql[j + 1] == "'":
                    j += 2
                    continue
                if sql[j] == "'":
                    break
                j += 1
            j = min(j + 1, n)
            lit = sql[i:j]
            out_nc.append(lit)
            inner = "".join("\n" if ch == "\n" else "_" for ch in lit[1:-1])
            out_m.append("'" + inner + ("'" if len(lit) > 1 else ""))
            i = j
        else:
            out_nc.append(c)
            out_m.append(c)
            i += 1
    return "".join(out_nc), "".join(out_m)


def line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def skip_parens(text: str, pos: int) -> int:
    """pos points at '('; return the index just after its matching ')'."""
    depth = 0
    for k in range(pos, len(text)):
        if text[k] == "(":
            depth += 1
        elif text[k] == ")":
            depth -= 1
            if depth == 0:
                return k + 1
    return len(text)


class Linter:
    def __init__(self, sql: str, dialect: str):
        self.raw = sql
        self.nc, self.m = mask(sql)
        self.low = self.m.lower()
        self.nc_low = self.nc.lower()
        self.dialect = dialect
        self.findings: List[dict] = []
        self.lines = sql.splitlines()

    def add(self, pos: int, rule: str, severity: str, message: str) -> None:
        ln = line_of(self.m, pos)
        snippet = self.lines[ln - 1].strip() if ln - 1 < len(self.lines) else ""
        self.findings.append(
            {"line": ln, "rule": rule, "severity": severity, "message": message, "snippet": snippet}
        )

    # --- rules -----------------------------------------------------------

    def select_star(self) -> None:
        pat = re.compile(r"(?:\bselect\s+(?:distinct\s+|all\s+)?|,\s*)((?:[\w`\"]+\.)?\*)(?!\s*\))")
        for mt in pat.finditer(self.low):
            self.add(
                mt.start(1), "select-star", "info",
                "SELECT * pulls every column: upstream column additions change the output, and in "
                "columnar warehouses you pay to scan columns you never use. List the columns.",
            )

    def not_in_subquery(self) -> None:
        for mt in re.finditer(r"\bnot\s+in\s*\(\s*select\b", self.low):
            self.add(
                mt.start(), "not-in-subquery", "warn",
                "NOT IN (subquery) returns zero rows if the subquery yields a single NULL. "
                "Use NOT EXISTS, or filter NULLs out of the subquery.",
            )

    def null_comparison(self) -> None:
        pat = re.compile(r"(?<![<>!:])(=|!=|<>)\s*null\b|\bnull\s*(=|!=|<>)")
        for mt in pat.finditer(self.low):
            self.add(
                mt.start(), "null-comparison", "error",
                "Comparing with = NULL or <> NULL is never true. Use IS NULL / IS NOT NULL "
                "(or IS DISTINCT FROM where the dialect has it).",
            )

    def join_without_condition(self) -> None:
        stop = re.compile(
            r"\b(join|where|group|order|limit|union|having|qualify|window|on|using)\b|[;()]"
        )
        for mt in re.finditer(r"\bjoin\b", self.low):
            before = self.low[max(0, mt.start() - 20):mt.start()]
            if re.search(r"\b(cross|natural)\s+$", before):
                continue
            pos = mt.end()
            after = self.low[pos:].lstrip()
            if re.match(r"(unnest|lateral|table\s*\()", after):
                continue
            found = None
            k = pos
            while k < len(self.low):
                s = stop.search(self.low, k)
                if not s:
                    break
                tok = s.group(0)
                if tok == "(":
                    k = skip_parens(self.low, s.start())
                    continue
                found = tok
                break
            if found not in ("on", "using"):
                self.add(
                    mt.start(), "join-without-condition", "error",
                    "JOIN with no ON or USING is a cross join: every row pairs with every row and "
                    "every SUM is multiplied. Add the join key, or write CROSS JOIN if you mean it.",
                )

    def comma_join(self) -> None:
        ident = r"[\w`\".]+"
        pat = re.compile(r"\bfrom\s+" + ident + r"(?:\s+(?:as\s+)?\w+)?\s*,\s*(" + ident + r")")
        for mt in pat.finditer(self.low):
            if mt.group(1).startswith("unnest"):
                continue
            self.add(
                mt.start(), "comma-join", "info",
                "Comma join in FROM: the join condition lives in WHERE, where it is easy to drop. "
                "Rewrite as an explicit JOIN ... ON.",
            )

    def between_timestamp(self) -> None:
        pat = re.compile(r"([\w.`\"]+)\s+between\s+(.+?)\s+and\s+([^\s)]+)", re.S)
        for mt in pat.finditer(self.nc_low):
            col = mt.group(1).strip("`\"").split(".")[-1]
            hi = mt.group(3)
            bare_date = re.match(r"'\d{4}-\d{2}-\d{2}'$", hi) is not None
            if TS_COL.search(col):
                msg = (
                    "BETWEEN on what looks like a timestamp column is inclusive at both ends. With a "
                    "bare-date upper bound it drops everything after midnight on the last day; with "
                    "a midnight upper bound it double-counts that instant across adjacent windows. "
                    "Use col >= start AND col < next_day."
                )
                self.add(mt.start(), "between-timestamp", "warn", msg)
            elif bare_date and not DATE_COL.search(col):
                msg = (
                    "BETWEEN with a bare-date upper bound: if '" + col + "' is a timestamp, the last "
                    "day is cut off at midnight. Check the column type; prefer >= start AND < next_day."
                )
                self.add(mt.start(), "between-timestamp", "info", msg)

    def integer_division(self) -> None:
        if self.dialect not in INT_DIVISION_DIALECTS:
            return
        for mt in re.finditer(r"\b(count|sum)\s*\(", self.low):
            end = skip_parens(self.low, mt.end() - 1)
            rest = self.low[end:end + 40]
            div = re.match(r"\s*/\s*(nullif\s*\(\s*)?(count|sum)\s*\(", rest)
            if not div:
                continue
            if mt.group(1) == "sum" and div.group(2) == "sum":
                continue
            before = self.low[max(0, mt.start() - 15):mt.start()]
            if re.search(r"(1\.0\s*\*|cast\s*\(\s*|::\s*\w*\s*)$", before) or rest.startswith("::"):
                continue
            sev = "warn" if (mt.group(1) == "count" and div.group(2) == "count") else "info"
            label = "COUNT / COUNT" if sev == "warn" else "SUM / COUNT"
            msg = (
                label + " in " + self.dialect + ": integer divided by integer truncates, so a 0.37 "
                "rate comes back as 0. Cast one side (::numeric, CAST(... AS DECIMAL), or * 1.0)."
            )
            if sev == "info":
                msg += " Only applies if the summed column is an integer type."
            self.add(mt.start(), "integer-division", sev, msg)

    def distinct_over_join(self) -> None:
        for mt in re.finditer(r"\bselect\s+distinct\b", self.low):
            # Scope = this SELECT up to the ')' closing its subquery/CTE, or ';'.
            depth = 0
            end = len(self.low)
            for k in range(mt.end(), len(self.low)):
                ch = self.low[k]
                if ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                    if depth < 0:
                        end = k
                        break
                elif ch == ";" and depth == 0:
                    end = k
                    break
            if not re.search(r"\bjoin\b", self.low[mt.end():end]):
                continue
            self.add(
                mt.start(), "distinct-over-join", "info",
                "SELECT DISTINCT in a query with joins: check it is not hiding a fan-out. DISTINCT "
                "removes the duplicate rows but SUM/COUNT computed before it are still inflated.",
            )

    def window_frames(self) -> None:
        pat = re.compile(r"\b(last_value|nth_value|sum|avg|count|min|max)\s*\(")
        for mt in pat.finditer(self.low):
            end = skip_parens(self.low, mt.end() - 1)
            over = re.match(r"\s*(ignore\s+nulls\s+|respect\s+nulls\s+)?over\s*\(", self.low[end:])
            if not over:
                continue
            ostart = end + over.end() - 1
            clause = self.low[ostart:skip_parens(self.low, ostart)]
            if "order by" not in clause or re.search(r"\b(rows|range|groups)\b", clause):
                continue
            fn = mt.group(1)
            if fn in ("last_value", "nth_value"):
                self.add(
                    mt.start(), "window-default-frame", "warn",
                    fn.upper() + " with ORDER BY and no frame uses the default frame, which ends at "
                    "the current row, so it returns the current row's value, not the partition's last. "
                    "Add ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING.",
                )
            else:
                self.add(
                    mt.start(), "window-default-frame", "info",
                    "Running " + fn.upper() + " with ORDER BY and no frame: in the SQL standard and "
                    "Postgres the default is RANGE, so rows that tie on the ORDER BY value share one "
                    "total. Write ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW if you want row by row.",
                )

    def where_clauses(self) -> List[Tuple[int, int]]:
        """WHERE bodies, ending at a clause keyword at the same paren depth,
        at the ')' that closes the enclosing subquery or CTE, or at ';'."""
        spans = []
        text = self.low
        for mt in re.finditer(r"\bwhere\b", text):
            start = mt.end()
            depth = 0
            k = start
            end = len(text)
            while k < len(text):
                ch = text[k]
                if ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                    if depth < 0:
                        end = k
                        break
                elif ch == ";" and depth == 0:
                    end = k
                    break
                elif depth == 0 and ch.isalpha() and (k == 0 or not (text[k - 1].isalnum() or text[k - 1] == "_")):
                    if CLAUSE_END.match(text, k):
                        end = k
                        break
                k += 1
            spans.append((start, end))
        return spans

    def left_join_where(self) -> None:
        pat = re.compile(r"\bleft\s+(?:outer\s+)?join\s+[\w`\".]+\s+(?:as\s+)?(\w+)")
        aliases = set()
        for mt in pat.finditer(self.low):
            a = mt.group(1)
            if a not in ("on", "using", "where"):
                aliases.add(a)
        if not aliases:
            return
        for start, end in self.where_clauses():
            body = self.low[start:end]
            for a in sorted(aliases):
                cmp = re.compile(
                    r"\b" + re.escape(a) + r"\.\w+\s*(=|<>|!=|>=|<=|>|<|\bin\b|\blike\b|\bbetween\b)"
                )
                for c in cmp.finditer(body):
                    self.add(
                        start + c.start(), "left-join-where-filter", "warn",
                        "WHERE filters on '" + a + "', the right side of a LEFT JOIN. Rows with no "
                        "match have NULL there and are dropped, so the LEFT JOIN behaves as an INNER "
                        "JOIN. Move the condition into the ON clause if you meant to keep them.",
                    )

    def non_sargable(self) -> None:
        fn = re.compile(
            r"\b(date|date_trunc|cast|lower|upper|extract|to_char|to_date|year|month|coalesce|"
            r"format_date|timestamp_trunc|convert)\s*\("
        )
        for start, end in self.where_clauses():
            body = self.low[start:end]
            for mt in fn.finditer(body):
                self.add(
                    start + mt.start(), "non-sargable-predicate", "info",
                    "Function wrapped around a column in WHERE: an index on that column usually "
                    "cannot be used, and in some warehouses partition pruning is lost. Compare the "
                    "bare column to a computed range instead (col >= x AND col < y).",
                )

    def union_distinct(self) -> None:
        for mt in re.finditer(r"\bunion\b(?!\s+all\b)", self.low):
            self.add(
                mt.start(), "union-dedup", "info",
                "UNION (without ALL) removes duplicate rows. If two sources can legitimately produce "
                "identical rows, counts and sums drop silently. Use UNION ALL unless you mean to dedupe.",
            )

    def run(self) -> List[dict]:
        for rule in (
            self.null_comparison, self.join_without_condition, self.not_in_subquery,
            self.between_timestamp, self.integer_division, self.window_frames,
            self.left_join_where, self.select_star, self.distinct_over_join,
            self.comma_join, self.non_sargable, self.union_distinct,
        ):
            rule()
        seen = set()
        uniq = []
        for f in self.findings:
            key = (f["line"], f["rule"])
            if key not in seen:
                seen.add(key)
                uniq.append(f)
        uniq.sort(key=lambda f: (f["line"], SEVERITY_ORDER[f["severity"]]))
        return uniq


def render_text(findings: List[dict], source: str, dialect: str) -> str:
    out = ["sql_lint: " + source + " (dialect: " + dialect + ")", ""]
    if not findings:
        out.append("No mechanical smells found. This does not mean the query is correct;")
        out.append("review joins, grain and date boundaries by reading it.")
        return "\n".join(out) + "\n"
    for f in findings:
        out.append("line %d  %-5s  %s" % (f["line"], f["severity"].upper(), f["rule"]))
        out.append("    > " + f["snippet"])
        out.append("    " + f["message"])
        out.append("")
    counts = {s: sum(1 for f in findings if f["severity"] == s) for s in SEVERITY_ORDER}
    out.append(
        "%d finding(s): %d error, %d warn, %d info"
        % (len(findings), counts["error"], counts["warn"], counts["info"])
    )
    return "\n".join(out) + "\n"


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Flag mechanical SQL smells that produce wrong numbers.")
    ap.add_argument("path", help="SQL file to lint, or - for stdin")
    ap.add_argument("--dialect", choices=DIALECTS, default="generic")
    ap.add_argument("--format", choices=("text", "json"), default="text")
    ap.add_argument("-o", "--out", help="write findings here instead of stdout")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any error or warn finding")
    args = ap.parse_args(argv)

    if args.path == "-":
        sql = sys.stdin.read()
        source = "<stdin>"
    else:
        try:
            with open(args.path, encoding="utf-8") as fh:
                sql = fh.read()
        except OSError as exc:
            print("error: cannot read " + args.path + ": " + exc.strerror, file=sys.stderr)
            return 2
        except UnicodeDecodeError:
            print("error: " + args.path + " is not UTF-8 text", file=sys.stderr)
            return 2
        source = args.path

    if not sql.strip():
        print("error: input is empty", file=sys.stderr)
        return 2
    _, masked = mask(sql)
    if not re.search(r"\b(select|with|insert|update|delete|merge)\b", masked, re.I):
        print("error: no SELECT/WITH/INSERT/UPDATE/DELETE/MERGE found; is this SQL?", file=sys.stderr)
        return 2

    findings = Linter(sql, args.dialect).run()
    if args.format == "json":
        text = json.dumps({"source": source, "dialect": args.dialect, "findings": findings}, indent=2) + "\n"
    else:
        text = render_text(findings, source, args.dialect)

    if args.out:
        try:
            with open(args.out, "w", encoding="utf-8") as fh:
                fh.write(text)
        except OSError as exc:
            print("error: cannot write " + args.out + ": " + exc.strerror, file=sys.stderr)
            return 2
        print("wrote " + str(len(findings)) + " finding(s) to " + args.out)
    else:
        sys.stdout.write(text)

    if args.strict and any(f["severity"] in ("error", "warn") for f in findings):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
