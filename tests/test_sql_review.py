import json
import os
import unittest

from tests.support import load, read, run, workdir, write

m = load("sql-review", "sql_lint.py")


def lint(sql, dialect="generic"):
    return [(f["line"], f["rule"], f["severity"]) for f in m.Linter(sql, dialect).run()]


def rules(sql, dialect="generic"):
    return {r for _, r, _ in lint(sql, dialect)}


class TestSqlLintRules(unittest.TestCase):
    def test_equals_null_is_an_error(self):
        self.assertEqual(lint("select id from t where x = null"), [(1, "null-comparison", "error")])

    def test_not_equals_null_is_an_error_but_is_null_is_fine(self):
        self.assertIn("null-comparison", rules("select id from t where y <> null"))
        self.assertIn("null-comparison", rules("select id from t where y != null"))
        self.assertEqual(lint("select id from t where x is null and y is not null"), [])

    def test_keywords_inside_strings_and_comments_are_ignored(self):
        sql = "select 'x = null join where' as label from t -- where y = null\n/* a join b */"
        self.assertEqual(lint(sql), [])

    def test_join_without_on_is_flagged_as_cross_join(self):
        self.assertEqual(lint("select a.id from a join b where a.x = 1"),
                         [(1, "join-without-condition", "error")])

    def test_join_with_on_using_or_explicit_cross_is_not_flagged(self):
        for sql in ("select a.id from a join b on a.id = b.id",
                    "select a.id from a left join b using (id)",
                    "select a.id from a cross join b",
                    "select a.id from a join (select id from c where c.x = 1) s on s.id = a.id"):
            with self.subTest(sql=sql):
                self.assertNotIn("join-without-condition", rules(sql))

    def test_not_in_subquery_warns(self):
        self.assertEqual(lint("select id from t where x not in (select y from u)"),
                         [(1, "not-in-subquery", "warn")])

    def test_between_on_timestamp_column_warns(self):
        sql = "select id from t where created_at between '2024-01-01' and '2024-01-31'"
        self.assertEqual(lint(sql), [(1, "between-timestamp", "warn")])

    def test_between_on_date_column_is_not_flagged(self):
        sql = "select id from t where order_date between '2024-01-01' and '2024-01-31'"
        self.assertEqual(lint(sql), [])

    def test_between_bare_date_on_unknown_column_is_info(self):
        sql = "select id from t where moment between '2024-01-01' and '2024-01-31'"
        self.assertEqual(lint(sql), [(1, "between-timestamp", "info")])

    def test_count_over_count_warns_in_postgres(self):
        self.assertEqual(lint("select count(x) / count(*) from t", "postgres"),
                         [(1, "integer-division", "warn")])

    def test_sum_over_count_is_info(self):
        self.assertEqual(lint("select sum(x) / count(*) from t", "postgres"),
                         [(1, "integer-division", "info")])

    def test_integer_division_is_skipped_where_division_is_float(self):
        for dialect in ("bigquery", "snowflake", "mysql"):
            with self.subTest(dialect=dialect):
                self.assertEqual(lint("select count(x) / count(*) from t", dialect), [])

    def test_cast_numerator_silences_integer_division(self):
        for sql in ("select count(x)::numeric / count(*) from t",
                    "select 1.0*count(x) / count(*) from t",
                    "select count(x) * 1.0 / count(*) from t",
                    "select cast(count(x) as numeric) / count(*) from t",
                    "select sum(a) / sum(b) from t"):
            with self.subTest(sql=sql):
                self.assertEqual(lint(sql, "postgres"), [])

    def test_spaced_one_point_zero_multiplier_silences_integer_division(self):
        self.assertEqual(lint("select 1.0 * count(x) / count(*) from t", "postgres"), [])

    def test_cast_denominator_silences_integer_division(self):
        self.assertEqual(lint("select count(x) / count(*)::float from t", "postgres"), [])

    def test_last_value_with_order_and_no_frame_warns(self):
        sql = "select last_value(x) over (partition by g order by d) from t"
        self.assertEqual(lint(sql), [(1, "window-default-frame", "warn")])

    def test_running_sum_with_no_frame_is_info_and_explicit_frame_is_clean(self):
        self.assertEqual(lint("select sum(x) over (order by d) from t"),
                         [(1, "window-default-frame", "info")])
        sql = "select sum(x) over (order by d rows between unbounded preceding and current row) from t"
        self.assertEqual(lint(sql), [])

    def test_where_filter_on_left_join_alias_warns(self):
        sql = "select a.id from a left join b bb on a.id = bb.a_id where bb.status = 'paid'"
        self.assertEqual(lint(sql), [(1, "left-join-where-filter", "warn")])

    def test_left_join_anti_join_is_null_is_not_flagged(self):
        sql = "select a.id from a left join b bb on a.id = bb.a_id where bb.a_id is null"
        self.assertEqual(lint(sql), [])

    def test_left_join_filter_inside_on_is_not_flagged(self):
        sql = "select a.id from a left join b bb on a.id = bb.a_id and bb.status = 'paid' where a.x = 1"
        self.assertEqual(lint(sql), [])

    def test_where_filter_on_unaliased_left_join_table_warns(self):
        sql = "select a.id from a left join orders on a.id = orders.a_id where orders.status = 'paid'"
        self.assertIn("left-join-where-filter", rules(sql))

    def test_select_star_is_info_but_count_star_is_not(self):
        self.assertEqual(lint("select * from t"), [(1, "select-star", "info")])
        self.assertEqual(lint("select t.* from t"), [(1, "select-star", "info")])
        self.assertEqual(lint("select count(*) from t"), [])

    def test_distinct_over_join_is_info(self):
        sql = "select distinct a.id from a join b on a.id = b.id"
        self.assertEqual(lint(sql), [(1, "distinct-over-join", "info")])
        self.assertEqual(lint("select distinct id from a"), [])

    def test_comma_join_is_info(self):
        self.assertEqual(lint("select a.id from a, b where a.id = b.id"), [(1, "comma-join", "info")])

    def test_function_on_column_in_where_is_non_sargable(self):
        sql = "select id from t where date(created_at) = '2024-01-01'"
        self.assertEqual(lint(sql), [(1, "non-sargable-predicate", "info")])
        self.assertEqual(lint("select id from t where y = 1 group by date(x)"), [])

    def test_union_without_all_is_flagged_once(self):
        sql = "select a from t\nunion\nselect a from u\nunion all\nselect a from v"
        self.assertEqual(lint(sql), [(2, "union-dedup", "info")])

    def test_findings_carry_line_numbers_and_sort_by_line_then_severity(self):
        sql = ("select *\n"
               "from a\n"
               "join b where a.x = null\n")
        self.assertEqual(lint(sql), [(1, "select-star", "info"),
                                     (3, "null-comparison", "error"),
                                     (3, "join-without-condition", "error")])

    def test_block_comment_keeps_line_numbers(self):
        sql = "/* one\ntwo\nthree */\nselect id from t where x = null"
        self.assertEqual(lint(sql), [(4, "null-comparison", "error")])

    def test_same_rule_on_same_line_reported_once(self):
        self.assertEqual(lint("select id from t where x = null or y = null"),
                         [(1, "null-comparison", "error")])


class TestSqlLintCli(unittest.TestCase):
    BAD = "select id from t where x = null\n"
    INFO_ONLY = "select * from t\n"

    def test_text_report_names_line_severity_rule_and_count(self):
        with workdir() as d:
            path = write(os.path.join(d, "q.sql"), self.BAD)
            code, out, _ = run("sql-review", "sql_lint.py", path, "--dialect", "postgres")
        self.assertEqual(code, 0)
        self.assertIn("(dialect: postgres)", out)
        self.assertIn("line 1  ERROR  null-comparison", out)
        self.assertIn("1 finding(s): 1 error, 0 warn, 0 info", out)

    def test_clean_query_says_no_smells_but_not_correct(self):
        code, out, _ = run("sql-review", "sql_lint.py", "-", stdin="select id from t where x = 1\n")
        self.assertEqual(code, 0)
        self.assertIn("No mechanical smells found", out)
        self.assertIn("<stdin>", out)

    def test_json_format_to_out_file(self):
        with workdir() as d:
            src = write(os.path.join(d, "q.sql"), self.BAD)
            dest = os.path.join(d, "findings.json")
            code, out, _ = run("sql-review", "sql_lint.py", src, "--format", "json", "-o", dest)
            doc = json.loads(read(dest))
        self.assertEqual(code, 0)
        self.assertIn("wrote 1 finding(s)", out)
        self.assertEqual(doc["dialect"], "generic")
        self.assertEqual([(f["line"], f["rule"], f["severity"]) for f in doc["findings"]],
                         [(1, "null-comparison", "error")])
        self.assertEqual(doc["findings"][0]["snippet"], "select id from t where x = null")

    def test_strict_exits_1_on_error_finding(self):
        code, _, _ = run("sql-review", "sql_lint.py", "-", "--strict", stdin=self.BAD)
        self.assertEqual(code, 1)

    def test_strict_exits_0_when_only_info_findings(self):
        code, _, _ = run("sql-review", "sql_lint.py", "-", "--strict", stdin=self.INFO_ONLY)
        self.assertEqual(code, 0)

    def test_without_strict_findings_still_exit_0(self):
        code, _, _ = run("sql-review", "sql_lint.py", "-", stdin=self.BAD)
        self.assertEqual(code, 0)

    def test_dialect_changes_integer_division_result(self):
        sql = "select count(x) / count(*) from t\n"
        code_pg, _, _ = run("sql-review", "sql_lint.py", "-", "--dialect", "postgres", "--strict", stdin=sql)
        code_bq, _, _ = run("sql-review", "sql_lint.py", "-", "--dialect", "bigquery", "--strict", stdin=sql)
        self.assertEqual((code_pg, code_bq), (1, 0))

    def test_missing_file_exits_2_with_message(self):
        with workdir() as d:
            code, out, err = run("sql-review", "sql_lint.py", os.path.join(d, "nope.sql"))
        self.assertEqual(code, 2)
        self.assertIn("cannot read", err)
        self.assertNotIn("Traceback", err)

    def test_empty_input_exits_2(self):
        code, _, err = run("sql-review", "sql_lint.py", "-", stdin="   \n")
        self.assertEqual(code, 2)
        self.assertIn("input is empty", err)

    def test_non_sql_input_exits_2(self):
        code, _, err = run("sql-review", "sql_lint.py", "-", stdin="hello world\n-- select\n")
        self.assertEqual(code, 2)
        self.assertIn("is this SQL?", err)

    def test_non_utf8_file_exits_2(self):
        with workdir() as d:
            path = os.path.join(d, "latin1.sql")
            with open(path, "wb") as fh:
                fh.write(b"select '\xe9' from t\n")
            code, _, err = run("sql-review", "sql_lint.py", path)
        self.assertEqual(code, 2)
        self.assertIn("not UTF-8", err)

    def test_unwritable_out_path_exits_2(self):
        with workdir() as d:
            dest = os.path.join(d, "no-such-dir", "out.json")
            code, _, err = run("sql-review", "sql_lint.py", "-", "-o", dest, stdin=self.BAD)
        self.assertEqual(code, 2)
        self.assertIn("cannot write", err)

    def test_unknown_dialect_is_rejected(self):
        code, _, err = run("sql-review", "sql_lint.py", "-", "--dialect", "oracle", stdin=self.BAD)
        self.assertEqual(code, 2)
        self.assertIn("invalid choice", err)


if __name__ == "__main__":
    unittest.main()
