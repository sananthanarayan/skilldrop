import json
import os
import unittest

from tests.support import load, run, workdir, write, read

SKILL, SCRIPT = "terraform-plan-review", "plan_summary.py"


def plan(*changes, **extra):
    doc = {"format_version": "1.2", "terraform_version": "1.9.5", "planned_values": {},
           "resource_changes": list(changes)}
    doc.update(extra)
    return doc


def rc(address, rtype, actions, before=None, after=None, **kw):
    change = {"actions": actions, "before": before, "after": after}
    change.update(kw.pop("change", {}))
    r = {"address": address, "type": rtype, "change": change}
    r.update(kw)
    return r


def policy(**statement):
    st = {"Effect": "Allow"}
    st.update(statement)
    return json.dumps({"Version": "2012-10-17", "Statement": [st]})


class PlanSummaryTest(unittest.TestCase):
    def setUp(self):
        self.m = load(SKILL, SCRIPT)

    def analyse(self, doc, scopes=()):
        return self.m.analyse(doc, list(scopes))

    def flagged(self, doc, scopes=()):
        return {f["address"]: f for f in self.analyse(doc, scopes)["flagged"]}

    # ---- verdicts

    def test_no_changes_is_safe_to_apply(self):
        r = self.analyse(plan())
        self.assertEqual(r["floor_verdict"], "SAFE TO APPLY")
        self.assertEqual(r["flagged"], [])

    def test_in_scope_update_of_stateless_resource_is_safe_and_not_flagged(self):
        doc = plan(rc("module.app.aws_instance.web", "aws_instance", ["update"],
                      {"instance_type": "t3.small"}, {"instance_type": "t3.medium"}))
        r = self.analyse(doc, ["module.app"])
        self.assertEqual(r["floor_verdict"], "SAFE TO APPLY")
        self.assertEqual(r["counts"], {"update": 1})

    def test_no_op_and_read_are_counted_but_not_flagged(self):
        doc = plan(rc("aws_vpc.main", "aws_vpc", ["no-op"]),
                   rc("data.aws_ami.base", "aws_ami", ["read"]))
        r = self.analyse(doc, ["module.app"])
        self.assertEqual(r["counts"], {"no-op": 1, "read": 1})
        self.assertEqual(r["floor_verdict"], "SAFE TO APPLY")

    def test_replaced_database_is_do_not_apply_with_forcing_attribute(self):
        doc = plan(rc("aws_db_instance.orders", "aws_db_instance", ["delete", "create"],
                      {"availability_zone": "eu-west-1a"}, {"availability_zone": "eu-west-1b"},
                      change={"replace_paths": [["availability_zone"]]},
                      action_reason="replace_because_cannot_update"))
        r = self.analyse(doc)
        self.assertEqual(r["floor_verdict"], "DO NOT APPLY")
        f = r["flagged"][0]
        self.assertEqual((f["action"], f["severity"]), ("replace (destroy then create)", 2))
        self.assertEqual(f["reasons"][0], "will be replaced; replacement forced by: availability_zone "
                                          "(action_reason: replace_because_cannot_update)")
        self.assertIn("stateful resource: data is lost unless a backup or snapshot exists", f["reasons"])

    def test_replace_path_with_list_index_is_formatted(self):
        self.assertEqual(self.m.fmt_path(["ebs_block_device", 0, "volume_size"]), "ebs_block_device[0].volume_size")
        self.assertEqual(self.m.fmt_path([]), "(root)")

    def test_replacing_stateless_resource_is_apply_with_care(self):
        doc = plan(rc("aws_instance.web", "aws_instance", ["create", "delete"], {}, {}))
        r = self.analyse(doc)
        self.assertEqual(r["floor_verdict"], "APPLY WITH CARE")
        self.assertEqual(r["flagged"][0]["action"], "replace (create then destroy)")
        self.assertEqual(r["flagged"][0]["reasons"], ["will be replaced"])

    def test_stateful_match_is_exact_unless_prefix_pattern(self):
        self.assertTrue(self.m.is_stateful("aws_s3_bucket"))
        self.assertFalse(self.m.is_stateful("aws_s3_bucket_policy"))
        self.assertTrue(self.m.is_stateful("aws_fsx_lustre_file_system"))
        self.assertTrue(self.m.is_stateful("azurerm_cosmosdb_account"))
        self.assertFalse(self.m.is_stateful("aws_instance"))

    def test_destroying_bucket_policy_is_care_but_destroying_bucket_is_do_not_apply(self):
        self.assertEqual(self.analyse(plan(rc("aws_s3_bucket_policy.p", "aws_s3_bucket_policy", ["delete"],
                                              {"bucket": "b"}, None)))["floor_verdict"], "APPLY WITH CARE")
        self.assertEqual(self.analyse(plan(rc("aws_s3_bucket.b", "aws_s3_bucket", ["delete"],
                                              {"bucket": "b"}, None)))["floor_verdict"], "DO NOT APPLY")

    def test_in_place_change_to_stateful_lists_attribute_names_never_values(self):
        doc = plan(rc("aws_db_instance.orders", "aws_db_instance", ["update"],
                      {"instance_class": "db.t3.small", "password": "not-a-real-password-1", "port": 5432},
                      {"instance_class": "db.t3.medium", "password": "not-a-real-password-2", "port": 5432}))
        r = self.analyse(doc)
        f = r["flagged"][0]
        self.assertEqual(r["floor_verdict"], "APPLY WITH CARE")
        self.assertEqual(f["reasons"], ["stateful resource changed in place"])
        self.assertEqual(f["changed_attributes"], ["instance_class", "password"])
        text = self.m.to_markdown(r) + json.dumps(r)
        for value in ("not-a-real-password", "db.t3.medium", "db.t3.small"):
            self.assertNotIn(value, text)

    # ---- access widening

    def test_new_ingress_from_anywhere_is_do_not_apply(self):
        doc = plan(rc("aws_security_group.web", "aws_security_group", ["create"], None,
                      {"ingress": [{"cidr_blocks": ["0.0.0.0/0"], "from_port": 22}],
                       "egress": [{"cidr_blocks": ["0.0.0.0/0"]}]}))
        f = self.analyse(doc)["flagged"][0]
        self.assertEqual(f["severity"], 2)
        self.assertEqual(f["reasons"], ["access widened: open CIDR 0.0.0.0/0"])

    def test_open_egress_alone_is_not_access_widening(self):
        doc = plan(rc("aws_security_group_rule.out", "aws_security_group_rule", ["create"], None,
                      {"type": "egress", "cidr_blocks": ["0.0.0.0/0"], "ipv6_cidr_blocks": ["::/0"]}),
                   rc("aws_vpc_security_group_egress_rule.out6", "aws_vpc_security_group_egress_rule",
                      ["create"], None, {"cidr_ipv6": "::/0"}))
        r = self.analyse(doc)
        self.assertEqual(r["floor_verdict"], "APPLY WITH CARE")
        for f in r["flagged"]:
            self.assertEqual(f["reasons"], ["access-control resource changed: read the before/after"])

    def test_wildcard_action_on_wildcard_resource_is_admin_and_do_not_apply(self):
        doc = plan(rc("aws_iam_policy.admin", "aws_iam_policy", ["create"], None,
                      {"policy": policy(Action="*", Resource="*")}))
        f = self.analyse(doc)["flagged"][0]
        self.assertEqual(f["severity"], 2)
        self.assertEqual(f["reasons"], ['access widened: policy allows Resource "*"; '
                                        "policy allows wildcard action *"])

    def test_service_wildcard_on_one_resource_is_care_only(self):
        doc = plan(rc("aws_iam_role_policy.s3", "aws_iam_role_policy", ["create"], None,
                      {"policy": policy(Action=["s3:*"], Resource="arn:aws:s3:::orders-bucket/*")}))
        r = self.analyse(doc)
        self.assertEqual(r["floor_verdict"], "APPLY WITH CARE")
        self.assertEqual(r["flagged"][0]["reasons"], ["access widened: policy allows wildcard action s3:*"])

    def test_public_principal_in_bucket_policy_is_do_not_apply(self):
        doc = plan(rc("aws_s3_bucket_policy.site", "aws_s3_bucket_policy", ["update"],
                      {"policy": policy(Action="s3:GetObject", Resource="arn:aws:s3:::site/*",
                                        Principal={"AWS": "arn:aws:iam::111122223333:root"})},
                      {"policy": policy(Action="s3:GetObject", Resource="arn:aws:s3:::site/*",
                                        Principal={"AWS": "*"})}))
        f = self.analyse(doc)["flagged"][0]
        self.assertEqual(f["severity"], 2)
        self.assertIn('policy allows Principal "*"', f["reasons"][0])

    def test_deny_statement_with_wildcards_is_not_widening(self):
        doc = plan(rc("aws_iam_policy.guard", "aws_iam_policy", ["create"], None,
                      {"policy": json.dumps({"Statement": {"Effect": "Deny", "Action": "*", "Resource": "*"}})}))
        f = self.analyse(doc)["flagged"][0]
        self.assertEqual(f["severity"], 1)
        self.assertEqual(f["reasons"], ["access-control resource changed: read the before/after"])

    def test_wildcard_already_present_before_is_not_new_widening(self):
        body = {"policy": policy(Action="*", Resource="*")}
        doc = plan(rc("aws_iam_policy.admin", "aws_iam_policy", ["update"], dict(body, name="a"),
                      dict(body, name="b")))
        f = self.analyse(doc)["flagged"][0]
        self.assertEqual(f["severity"], 1)
        self.assertEqual(f["reasons"], ["access-control resource changed: read the before/after"])

    def test_public_access_block_turned_off_is_do_not_apply(self):
        doc = plan(rc("aws_s3_bucket_public_access_block.b", "aws_s3_bucket_public_access_block", ["update"],
                      {"block_public_policy": True, "block_public_acls": True},
                      {"block_public_policy": False, "block_public_acls": True}))
        r = self.analyse(doc)
        self.assertEqual(r["floor_verdict"], "DO NOT APPLY")
        self.assertIn("access widened: block_public_policy turned off", r["flagged"][0]["reasons"])

    def test_deletion_protection_turned_off_is_care(self):
        doc = plan(rc("aws_lb.public", "aws_lb", ["update"],
                      {"enable_deletion_protection": True}, {"enable_deletion_protection": False}))
        r = self.analyse(doc)
        self.assertEqual(r["floor_verdict"], "APPLY WITH CARE")
        self.assertEqual(r["flagged"][0]["reasons"], ["enable_deletion_protection turned off"])

    # ---- scope, drift, import, forget, errored

    def test_in_scope_matches_prefix_only_at_address_boundaries(self):
        scopes = ["module.api"]
        self.assertTrue(self.m.in_scope("module.api.aws_lb.public", scopes))
        self.assertTrue(self.m.in_scope('module.api["blue"].aws_lb.public', scopes))
        self.assertTrue(self.m.in_scope("module.api", scopes))
        self.assertFalse(self.m.in_scope("module.api_v2.aws_lb.public", scopes))
        self.assertTrue(self.m.in_scope("anything", []))

    def test_out_of_scope_create_is_flagged(self):
        doc = plan(rc("module.api.aws_instance.a", "aws_instance", ["create"], None, {}),
                   rc("module.billing.aws_instance.b", "aws_instance", ["create"], None, {}))
        r = self.analyse(doc, ["module.api"])
        self.assertEqual(r["floor_verdict"], "APPLY WITH CARE")
        self.assertEqual([f["address"] for f in r["flagged"]], ["module.billing.aws_instance.b"])
        self.assertEqual(r["flagged"][0]["reasons"], ["outside the stated scope"])

    def test_drift_alone_makes_apply_with_care(self):
        doc = plan(resource_drift=[rc("aws_instance.web", "aws_instance", ["update"],
                                      {"instance_type": "t3.small", "tags": {}},
                                      {"instance_type": "t3.large", "tags": {}})])
        r = self.analyse(doc)
        self.assertEqual(r["floor_verdict"], "APPLY WITH CARE")
        self.assertEqual(r["drift"], [{"address": "aws_instance.web", "action": "update",
                                       "changed_attributes": ["instance_type"]}])

    def test_import_and_forget_are_flagged_care(self):
        doc = plan(rc("aws_instance.legacy", "aws_instance", ["update"], {}, {},
                      change={"importing": {"id": "i-0fake"}}),
                   rc("aws_instance.old", "aws_instance", ["forget"], {}, None))
        f = self.flagged(doc)
        self.assertIn("import: Terraform will take over an existing object", f["aws_instance.legacy"]["reasons"])
        self.assertEqual(f["aws_instance.old"]["reasons"],
                         ["forget: removed from state, the real object is left running"])
        self.assertEqual(self.analyse(doc)["floor_verdict"], "APPLY WITH CARE")

    def test_errored_plan_is_do_not_apply(self):
        r = self.analyse(plan(errored=True))
        self.assertEqual(r["floor_verdict"], "DO NOT APPLY")
        self.assertIn("The plan errored", self.m.to_markdown(r))

    def test_deposed_object_address_is_labelled(self):
        doc = plan(rc("aws_instance.web", "aws_instance", ["delete"], {}, None, deposed="00fake01"))
        self.assertIn("aws_instance.web (deposed object 00fake01)", self.flagged(doc))

    def test_changed_keys_skips_computed_attributes_new_on_this_change(self):
        change = {"before": {"ami": "ami-1", "arn": "x"}, "after": {"ami": "ami-1"},
                  "after_unknown": {"arn": True, "public_ip": True}}
        self.assertEqual(self.m.changed_keys(change), ["arn"])

    def test_flagged_sorted_by_severity_then_address(self):
        doc = plan(rc("aws_instance.b", "aws_instance", ["delete"], {}, None),
                   rc("aws_instance.a", "aws_instance", ["delete"], {}, None),
                   rc("aws_ebs_volume.z", "aws_ebs_volume", ["delete"], {}, None))
        self.assertEqual([f["address"] for f in self.analyse(doc)["flagged"]],
                         ["aws_ebs_volume.z", "aws_instance.a", "aws_instance.b"])

    # ---- CLI

    def test_markdown_counts_row_and_verdict(self):
        doc = plan(rc("aws_instance.new", "aws_instance", ["create"], None, {}),
                   rc("aws_instance.up", "aws_instance", ["update"], {"a": 1}, {"a": 2}),
                   rc("aws_instance.r1", "aws_instance", ["delete", "create"], {}, {}),
                   rc("aws_instance.r2", "aws_instance", ["create", "delete"], {}, {}),
                   rc("aws_instance.gone", "aws_instance", ["delete"], {}, None),
                   rc("aws_vpc.main", "aws_vpc", ["no-op"]))
        with workdir() as d:
            code, out, err = run(SKILL, SCRIPT, write(os.path.join(d, "plan.json"), json.dumps(doc)),
                                 "--scope", "aws_instance")
        self.assertEqual(code, 0, err)
        self.assertIn("**Floor verdict: APPLY WITH CARE**", out)
        self.assertIn("| 1 | 1 | 2 | 1 | 0 | 0 | 1 |", out)
        self.assertIn("Scope: aws_instance", out)
        self.assertIn("- [CARE] `aws_instance.gone` (delete)", out)

    def test_json_format_from_stdin(self):
        code, out, err = run(SKILL, SCRIPT, "-", "--format", "json", stdin=json.dumps(plan()))
        self.assertEqual(code, 0, err)
        r = json.loads(out)
        self.assertEqual((r["floor_verdict"], r["terraform_version"]), ("SAFE TO APPLY", "1.9.5"))

    def test_out_flag_writes_file(self):
        with workdir() as d:
            target = os.path.join(d, "summary.md")
            code, out, err = run(SKILL, SCRIPT, write(os.path.join(d, "p.json"), json.dumps(plan())),
                                 "-o", target)
            self.assertEqual(code, 0, err)
            self.assertEqual(out, "")
            self.assertIn("wrote", err)
            self.assertIn("None flagged.", read(target))

    # ---- bad input: exit 2 with a message

    def assert_rejected(self, text, needle):
        with workdir() as d:
            code, out, err = run(SKILL, SCRIPT, write(os.path.join(d, "in.json"), text))
        self.assertEqual(code, 2, out)
        self.assertIn(needle, err)
        self.assertNotIn("Traceback", err)

    def test_missing_file_exits_2(self):
        with workdir() as d:
            code, _, err = run(SKILL, SCRIPT, os.path.join(d, "absent.json"))
        self.assertEqual(code, 2)
        self.assertIn("cannot read", err)

    def test_empty_input_exits_2(self):
        self.assert_rejected("  \n", "input is empty")

    def test_human_readable_plan_text_exits_2_with_conversion_hint(self):
        self.assert_rejected("Terraform will perform the following actions:\n\nPlan: 1 to add, 0 to change.\n",
                             "terraform show -json tfplan")

    def test_invalid_json_exits_2(self):
        self.assert_rejected('{"format_version": ', "not valid JSON")

    def test_json_without_format_version_exits_2(self):
        self.assert_rejected('{"resource_changes": []}', "no format_version")

    def test_state_file_exits_2(self):
        self.assert_rejected('{"format_version": "1.0", "values": {}}', "state file")

    def test_resource_changes_not_a_list_exits_2(self):
        self.assert_rejected('{"format_version": "1.2", "resource_changes": {}}', "not a list")

    def test_non_utf8_plan_exits_2_without_traceback(self):
        with workdir() as d:
            path = os.path.join(d, "utf16.json")
            with open(path, "w", encoding="utf-16") as f:
                f.write(json.dumps(plan()))
            code, _, err = run(SKILL, SCRIPT, path)
        self.assertEqual(code, 2)
        self.assertNotIn("Traceback", err)


if __name__ == "__main__":
    unittest.main()
