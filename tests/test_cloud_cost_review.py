import json
import os
import unittest
from pathlib import Path

from tests.support import load, run, workdir, write, read

SKILL, SCRIPT = "cloud-cost-review", "cost_summary.py"
m = load(SKILL, SCRIPT)

GENERIC = """date,cost,service,account,region,usage_type,resource_id,line_type,pricing_model,tag_team
2026-08-01,100,EC2,111,us-east-1,BoxUsage:m5.large,i-1,usage,on_demand,web
2026-08-01,50,S3,111,us-east-1,TimedStorage-ByteHrs,bucket-a,usage,,
2026-09-01,150,EC2,111,us-east-1,BoxUsage:m5.large,i-1,usage,on_demand,web
2026-09-01,60,EC2,111,us-east-1,BoxUsage:m5.large,i-2,usage,commitment,
2026-09-01,40,S3,111,us-east-1,TimedStorage-ByteHrs,bucket-a,usage,,
2026-09-01,10,DataTransfer,111,us-east-1,DataTransfer-Out-Bytes,,usage,,
2026-09-01,20,Tax,111,,,,tax,,
2026-09-01,-25,Credits,111,,,,credit,,
"""

AWS_CUR = """lineItem/UsageStartDate,lineItem/UnblendedCost,lineItem/LineItemType,lineItem/UsageType,product/ProductName,lineItem/UsageAccountId,lineItem/ResourceId,savingsPlan/SavingsPlanEffectiveCost,resourceTags/user:team
2026-08-01T00:00:00Z,276.48,Usage,BoxUsage:m6i.2xlarge,Amazon Elastic Compute Cloud,111111111111,i-a,,web
2026-09-01T00:00:00Z,276.48,Usage,BoxUsage:m6i.2xlarge,Amazon Elastic Compute Cloud,111111111111,i-a,,web
2026-09-01T00:00:00Z,276.48,SavingsPlanCoveredUsage,BoxUsage:m6i.2xlarge,Amazon Elastic Compute Cloud,111111111111,i-b,190.80,
2026-09-01T00:00:00Z,-276.48,SavingsPlanNegation,BoxUsage:m6i.2xlarge,Amazon Elastic Compute Cloud,111111111111,i-b,,
2026-09-01T00:00:00Z,200,SavingsPlanRecurringFee,ComputeSP:1yrNoUpfront,Savings Plans for AWS Compute usage,111111111111,,,
2026-09-01T00:00:00Z,30,Tax,,Amazon Elastic Compute Cloud,111111111111,,,
2026-09-01T00:00:00Z,-50,Credit,,Amazon Elastic Compute Cloud,111111111111,,,
2026-09-01T00:00:00Z,20,Usage,USE1-SpotUsage:m5.large,Amazon Elastic Compute Cloud,111111111111,i-c,,
2026-09-01T00:00:00Z,99,Usage,USE1-NatGateway-Bytes,Amazon Elastic Compute Cloud,111111111111,nat-1,,
"""


def analyse_text(d, text, tags=(), month=None, top=10, fmt="auto", name="cost.csv"):
    path = write(os.path.join(d, name), text)
    fmt, used, rows = m.load(Path(path), fmt)
    return fmt, used, m.analyse(rows, list(tags), month, top, fmt)


def daily_rows(month, days, cost_for_day, service="EC2", usage="BoxUsage:m5.large",
               pricing="on_demand"):
    return "".join("%s-%02d,%s,%s,111,us-east-1,%s,i-1,usage,%s,\n"
                   % (month, dd, cost_for_day(dd), service, usage, pricing)
                   for dd in range(1, days + 1))


HEADER = "date,cost,service,account,region,usage_type,resource_id,line_type,pricing_model,tag_team\n"


class CostSummaryAnalysisTests(unittest.TestCase):
    def test_generic_month_over_month_usage_excludes_tax_and_credits(self):
        with workdir() as d:
            fmt, _, a = analyse_text(d, GENERIC)
        self.assertEqual(fmt, "generic")
        self.assertEqual((a["current_month"], a["previous_month"]), ("2026-09", "2026-08"))
        h = a["headline"]
        self.assertEqual((h["usage_cost_current"], h["usage_cost_previous"]), (260.0, 150.0))
        self.assertEqual(h["change"], 110.0)
        self.assertEqual(h["change_pct"], 0.7333)
        self.assertEqual(h["basis"], "monthly totals")
        self.assertEqual(a["non_usage_lines"]["tax"]["current"], 20.0)
        self.assertEqual(a["non_usage_lines"]["credit"]["current"], -25.0)

    def test_by_service_ranked_with_change_and_new_status(self):
        with workdir() as d:
            _, _, a = analyse_text(d, GENERIC)
        svc = {x["key"]: x for x in a["by_service"]}
        self.assertEqual([x["key"] for x in a["by_service"]], ["EC2", "S3", "DataTransfer"])
        self.assertEqual((svc["EC2"]["current"], svc["EC2"]["change"], svc["EC2"]["change_pct"]),
                         (210.0, 110.0, 1.1))
        self.assertEqual(svc["S3"]["change"], -10.0)
        self.assertEqual(svc["DataTransfer"]["status"], "new")
        self.assertEqual(a["top_movers"][0]["key"], "EC2 / BoxUsage:m5.large")

    def test_untagged_share_of_all_spend_and_of_spend_with_resource_id(self):
        with workdir() as d:
            _, _, a = analyse_text(d, GENERIC, tags=["team"])
        sep = a["tags"]["team"]["by_month"]["2026-09"]
        self.assertEqual(sep["untagged_cost"], 110.0)            # 60 + 40 + 10
        self.assertEqual(sep["untagged_share"], 0.4231)          # 110 / 260
        self.assertEqual(sep["untagged_share_of_taggable"], 0.4)  # 100 / 250
        self.assertEqual(sep["spend_without_resource_id"], 10.0)
        aug = a["tags"]["team"]["by_month"]["2026-08"]
        self.assertEqual(aug["untagged_share"], 0.3333)

    def test_missing_tag_key_is_noted(self):
        with workdir() as d:
            _, _, a = analyse_text(d, GENERIC, tags=["cost-center"])
        self.assertTrue(any("None of the requested tag keys (cost-center)" in n
                            and "team" in n for n in a["notes"]))

    def test_generic_commitment_coverage(self):
        with workdir() as d:
            _, _, a = analyse_text(d, GENERIC)
        c = a["commitments"]
        self.assertEqual(c["compute_on_demand"], 150.0)
        self.assertEqual(c["compute_covered_on_demand_equivalent"], 60.0)
        self.assertEqual(c["coverage"], 0.2857)

    def test_hot_spots_categorise_transfer_and_storage(self):
        with workdir() as d:
            _, _, a = analyse_text(d, GENERIC)
        self.assertEqual(a["hot_spots"]["data_transfer"]["current"], 10.0)
        self.assertEqual(a["hot_spots"]["storage"]["current"], 40.0)
        self.assertEqual(a["hot_spots"]["storage"]["previous"], 50.0)
        self.assertEqual(a["hot_spots"]["nat_gateway"]["current"], 0.0)

    def test_monthly_grain_is_noted_and_has_no_floor(self):
        with workdir() as d:
            _, _, a = analyse_text(d, GENERIC)
        self.assertTrue(any("export looks monthly" in n for n in a["notes"]))
        self.assertNotIn("daily_on_demand_compute_min", a["commitments"])

    def test_partial_month_compares_average_daily_spend(self):
        text = HEADER + daily_rows("2026-08", 31, lambda dd: 10) + \
            daily_rows("2026-09", 10, lambda dd: 12)
        with workdir() as d:
            _, _, a = analyse_text(d, text)
        h = a["headline"]
        self.assertEqual((h["usage_cost_current"], h["usage_cost_previous"]), (120.0, 310.0))
        self.assertEqual(h["change"], 2.0)       # $12/day vs $10/day, not -$190
        self.assertEqual(h["change_pct"], 0.2)
        self.assertTrue(h["basis"].startswith("average daily spend"))
        self.assertTrue(any("2026-09: 10 of 30 days" in n for n in a["notes"]))

    def test_steady_on_demand_floor_from_daily_data(self):
        text = HEADER + daily_rows("2026-09", 30, lambda dd: dd)  # $1..$30 a day
        with workdir() as d:
            _, _, a = analyse_text(d, text)
        c = a["commitments"]
        self.assertEqual(c["daily_on_demand_compute_min"], 1.0)
        self.assertEqual(c["daily_on_demand_compute_p10"], 4.0)
        self.assertEqual(c["daily_on_demand_compute_median"], 16.0)
        self.assertEqual(c["daily_on_demand_min_by_service"], {"EC2": 1.0})
        self.assertTrue(any("No month before 2026-09" in n for n in a["notes"]))

    def test_month_flag_selects_earlier_month(self):
        with workdir() as d:
            _, _, a = analyse_text(d, GENERIC, month="2026-08")
        self.assertEqual(a["current_month"], "2026-08")
        self.assertIsNone(a["previous_month"])
        self.assertEqual(a["headline"]["usage_cost_current"], 150.0)

    def test_gap_between_months_is_noted(self):
        text = HEADER + "2026-07-01,5,EC2,1,r,BoxUsage:x,i,usage,on_demand,\n" \
                        "2026-09-01,5,EC2,1,r,BoxUsage:x,i,usage,on_demand,\n"
        with workdir() as d:
            _, _, a = analyse_text(d, text)
        self.assertTrue(any("not the calendar month before" in n for n in a["notes"]))

    def test_negative_usage_lines_are_noted(self):
        text = HEADER + "2026-09-01,-5,EC2,1,r,BoxUsage:x,i,usage,on_demand,\n"
        with workdir() as d:
            _, _, a = analyse_text(d, text)
        self.assertTrue(any("negative cost" in n for n in a["notes"]))

    def test_aws_cur_uses_effective_cost_and_separates_fees(self):
        with workdir() as d:
            fmt, used, a = analyse_text(d, AWS_CUR, tags=["team"])
        self.assertEqual(fmt, "aws-cur")
        self.assertEqual(a["headline"]["usage_cost_current"], 586.28)  # 276.48+190.80+20+99
        other = a["non_usage_lines"]
        self.assertEqual(other["skip"]["current"], -276.48)
        self.assertEqual(other["commitment_fee"]["current"], 200.0)
        self.assertEqual(other["tax"]["current"], 30.0)
        self.assertEqual(other["credit"]["current"], -50.0)
        self.assertEqual(a["tag_keys_in_data"], ["team"])

    def test_aws_cur_coverage_and_utilisation(self):
        with workdir() as d:
            _, _, a = analyse_text(d, AWS_CUR)
        c = a["commitments"]
        self.assertEqual(c["compute_on_demand"], 276.48)
        self.assertEqual(c["compute_covered_on_demand_equivalent"], 276.48)
        self.assertEqual(c["compute_covered_effective_cost"], 190.8)
        self.assertEqual(c["coverage"], 0.5)
        self.assertEqual(c["utilisation_estimate"], 0.954)  # 190.80 / 200
        self.assertEqual(a["hot_spots"]["nat_gateway"]["current"], 99.0)

    # BUG: AWS spot usage types (SpotUsage:...) never match COMPUTE_RE, so compute_spot is always $0.
    @unittest.expectedFailure
    def test_aws_spot_compute_is_counted(self):
        with workdir() as d:
            _, _, a = analyse_text(d, AWS_CUR)
        self.assertEqual(a["commitments"]["compute_spot"], 20.0)

    def test_aws_cur2_detected_with_json_tags(self):
        text = ("line_item_usage_start_date,line_item_unblended_cost,line_item_line_item_type,"
                "line_item_usage_type,product_product_name,resource_tags\n"
                '2026-09-01,12.5,Usage,BoxUsage:t3.micro,Amazon EC2,"{""user:team"": ""api""}"\n')
        with workdir() as d:
            fmt, _, a = analyse_text(d, text, tags=["team"])
        self.assertEqual(fmt, "aws-cur2")
        self.assertEqual(a["tags"]["team"]["by_value"][0]["key"], "api")

    def test_gcp_nets_credits_and_lists_commitment_sku_as_fee(self):
        text = ("usage_start_time,project_id,service_description,sku_description,cost,credits_total,"
                "labels,cost_type\n"
                '2026-09-01,proj-a,Compute Engine,N2 Instance Core running in Americas,100,-10,'
                '"[{""key"": ""team"", ""value"": ""web""}]",regular\n'
                "2026-09-01,proj-a,Compute Engine,Commitment v1: N2 Cpu in Americas,30,0,,regular\n"
                "2026-09-01,proj-a,Tax,Tax,5,0,,tax\n")
        with workdir() as d:
            fmt, _, a = analyse_text(d, text, tags=["team"])
        self.assertEqual(fmt, "gcp")
        self.assertEqual(a["headline"]["usage_cost_current"], 90.0)
        self.assertEqual(a["non_usage_lines"]["commitment_fee"]["current"], 30.0)
        self.assertEqual(a["non_usage_lines"]["tax"]["current"], 5.0)
        self.assertIsNone(a["commitments"]["coverage"])
        self.assertTrue(any("Commitment coverage not computed" in n for n in a["notes"]))
        self.assertEqual(a["tags"]["team"]["by_month"]["2026-09"]["untagged_cost"], 0.0)

    def test_azure_pricing_models_unused_reservation_and_braceless_tags(self):
        text = ("date,meterCategory,meterSubCategory,meterName,costInBillingCurrency,"
                "subscriptionName,chargeType,pricingModel,tags,resourceId\n"
                '09/01/2026,Virtual Machines,Dv3 Series,D2 v3,100,sub-a,Usage,OnDemand,'
                '"""team"": ""web""",/subs/vm1\n'
                "09/01/2026,Virtual Machines,Dv3 Series,D2 v3,40,sub-a,Usage,Reservation,,/subs/vm2\n"
                "09/01/2026,Virtual Machines,,,10,sub-a,UnusedReservation,Reservation,,\n"
                "09/01/2026,Virtual Machines,,,300,sub-a,Purchase,Reservation,,\n")
        with workdir() as d:
            fmt, _, a = analyse_text(d, text, tags=["team"])
        self.assertEqual(fmt, "azure")
        self.assertEqual(a["headline"]["usage_cost_current"], 150.0)
        c = a["commitments"]
        self.assertEqual(c["unused_commitment_lines"], 10.0)
        self.assertEqual(c["commitment_fees"], 300.0)
        self.assertEqual(c["coverage"], 0.2857)  # 40 / (40 + 100)
        self.assertEqual(a["tag_keys_in_data"], ["team"])
        self.assertEqual(a["top_resources"][0]["key"], "/subs/vm1 / Virtual Machines / Dv3 Series D2 v3")


class CostSummaryCliTests(unittest.TestCase):
    def test_writes_markdown_and_json(self):
        with workdir() as d:
            src = write(os.path.join(d, "cost.csv"), GENERIC)
            md, js = os.path.join(d, "out", "s.md"), os.path.join(d, "out", "s.json")
            code, out, err = run(SKILL, SCRIPT, src, "--tag", "team", "--out", md, "--json", js)
            self.assertEqual(code, 0, err)
            report, data = read(md), json.loads(read(js))
        self.assertIn("# Cloud cost summary: 2026-09 vs 2026-08", report)
        self.assertIn("| Usage cost | $260.00 | $150.00 | $110.00 (+73.3%) |", report)
        self.assertIn("## Tag `team`", report)
        self.assertIn("## Column mapping used", report)
        self.assertEqual(data["format"], "generic")
        self.assertEqual(data["headline"]["usage_cost_current"], 260.0)

    def test_partial_month_report_labels_change_per_day(self):
        text = HEADER + daily_rows("2026-08", 31, lambda dd: 10) + \
            daily_rows("2026-09", 10, lambda dd: 12)
        with workdir() as d:
            code, out, err = run(SKILL, SCRIPT, write(os.path.join(d, "c.csv"), text))
        self.assertEqual(code, 0, err)
        self.assertIn("Change per day", out)

    def test_forced_format_that_does_not_fit_exits_2(self):
        with workdir() as d:
            code, _, err = run(SKILL, SCRIPT, write(os.path.join(d, "c.csv"), GENERIC),
                               "--format", "aws-cur")
        self.assertEqual(code, 2)
        self.assertIn("no date column found", err)

    def test_bad_inputs_exit_2_with_message(self):
        cases = {
            "unknown.csv": ("when,amount\n2026-09-01,1\n", "cannot recognise the export format"),
            "empty.csv": ("", "empty or has no header row"),
            "header_only.csv": ("date,cost\n", "header but no rows"),
            "bad_cost.csv": ("date,cost\n2026-09-01,abc\n", "line 2: cost value 'abc' is not a number"),
            "bad_date.csv": ("date,cost\n2026-09-01,1\nyesterday,2\n", "line 3: cannot read date"),
            "bad_day.csv": ("date,cost\n2026-02-30,1\n", "invalid date"),
        }
        with workdir() as d:
            for name, (text, msg) in cases.items():
                code, _, err = run(SKILL, SCRIPT, write(os.path.join(d, name), text))
                self.assertEqual(code, 2, name)
                self.assertIn(msg, err, name)
                self.assertNotIn("Traceback", err, name)
            code, _, err = run(SKILL, SCRIPT, os.path.join(d, "missing.csv"))
            self.assertEqual(code, 2)
            self.assertIn("file not found", err)

    def test_bad_month_and_top_flags_exit_2(self):
        with workdir() as d:
            src = write(os.path.join(d, "c.csv"), GENERIC)
            for args, msg in ((["--month", "2026-9"], "--month must be YYYY-MM"),
                              (["--month", "2026-01"], "not in the data"),
                              (["--top", "0"], "--top must be at least 1")):
                code, _, err = run(SKILL, SCRIPT, src, *args)
                self.assertEqual(code, 2, args)
                self.assertIn(msg, err, args)

    # BUG: a non-UTF-8 export (e.g. a cp1252 CSV saved by Excel) crashes with a UnicodeDecodeError traceback instead of exit 2.
    @unittest.expectedFailure
    def test_non_utf8_export_exits_2(self):
        with workdir() as d:
            path = os.path.join(d, "latin1.csv")
            with open(path, "wb") as f:
                f.write("date,cost,service\n2026-09-01,10,Café\n".encode("latin-1"))
            code, _, err = run(SKILL, SCRIPT, path)
        self.assertEqual(code, 2)
        self.assertNotIn("Traceback", err)


if __name__ == "__main__":
    unittest.main()
