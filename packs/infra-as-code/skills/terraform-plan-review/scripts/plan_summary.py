#!/usr/bin/env python3
"""Summarise a Terraform JSON plan and list the changes a reviewer must look at. Stdlib only.

Input is the machine-readable plan that `terraform show -json <planfile>` prints (the
documented JSON output format: resource_changes[], each with change.actions, and
replace_paths / action_reason when a resource is replaced; resource_drift[] for objects
that changed outside Terraform). The script never calls Terraform and never prints
attribute values, so sensitive values in the plan stay out of its output.

Usage:
  terraform plan -out=tfplan && terraform show -json tfplan > plan.json
  python3 plan_summary.py plan.json [--scope module.api --scope aws_lb.public] [-o summary.md]
  terraform show -json tfplan | python3 plan_summary.py - [--format json]

Exit codes: 0 summary written; 2 bad input (not JSON, not a plan, unreadable file).
The floor verdict is mechanical: the reviewer reads every flagged change and may raise it,
or lower it only when the user confirms the change is intended and recoverable.
"""
import argparse
import json
import re
import sys

# Resource types that hold data: a delete or replace loses it unless there is a backup.
# An entry ending in "_" matches as a prefix (a family of types); any other entry must equal
# the resource type, so aws_s3_bucket does not also match aws_s3_bucket_policy.
STATEFUL_PATTERNS = (
    "aws_db_instance", "aws_rds_cluster", "aws_neptune_cluster", "aws_docdb_cluster",
    "aws_dynamodb_table", "aws_s3_bucket", "aws_s3_directory_bucket", "aws_ebs_volume",
    "aws_efs_file_system", "aws_fsx_", "aws_elasticache_cluster", "aws_elasticache_replication_group",
    "aws_elasticache_serverless_cache", "aws_memorydb_cluster", "aws_redshift_cluster",
    "aws_opensearch_domain", "aws_elasticsearch_domain", "aws_msk_cluster", "aws_kinesis_stream",
    "aws_sqs_queue", "aws_kms_key", "aws_secretsmanager_secret", "aws_backup_vault",
    "google_sql_database_instance", "google_sql_database", "google_storage_bucket",
    "google_compute_disk", "google_bigquery_dataset", "google_bigquery_table",
    "google_spanner_instance", "google_spanner_database", "google_bigtable_instance",
    "google_bigtable_table", "google_redis_instance", "google_filestore_instance",
    "google_kms_crypto_key", "google_pubsub_topic", "google_pubsub_subscription",
    "azurerm_storage_account", "azurerm_storage_container", "azurerm_mssql_server",
    "azurerm_mssql_database", "azurerm_mssql_managed_instance", "azurerm_postgresql_server",
    "azurerm_postgresql_flexible_server", "azurerm_postgresql_flexible_server_database",
    "azurerm_mysql_flexible_server", "azurerm_mysql_flexible_database", "azurerm_cosmosdb_",
    "azurerm_managed_disk", "azurerm_redis_cache", "azurerm_key_vault",
)

# Resource types that grant access or open network paths.
ACCESS_PATTERNS = (
    "_iam_", "iam_policy", "iam_role", "_security_group", "_firewall", "network_security",
    "_role_assignment", "_policy_attachment", "bucket_policy", "_bucket_acl", "public_access_block",
    "_kms_grant", "_key_policy", "_lambda_permission", "_network_acl",
)

OPEN_CIDRS = ("0.0.0.0/0", "::/0")
# Attributes where true means "protected"; a true -> false change removes a safety net.
PROTECTION_FLAGS = ("deletion_protection", "enable_deletion_protection", "deletion_protection_enabled",
                    "disable_api_termination")
# S3 public access block settings; true -> false opens the bucket or account to public access.
PUBLIC_BLOCK_FLAGS = ("block_public_acls", "block_public_policy", "ignore_public_acls",
                      "restrict_public_buckets")


def die(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(2)


def load_plan(path):
    try:
        raw = sys.stdin.read() if path == "-" else open(path, encoding="utf-8").read()
    except OSError as e:
        die(f"cannot read {path}: {e.strerror}")
    stripped = raw.lstrip()
    if not stripped:
        die("input is empty")
    if not stripped.startswith("{"):
        if re.search(r"Terraform will perform|Plan: \d+ to add|No changes\.", raw):
            die("this is the human-readable plan text. Save the plan and convert it: "
                "terraform plan -out=tfplan && terraform show -json tfplan > plan.json "
                "(or review the text by hand, following the skill's SKILL.md)")
        die("input is not JSON")
    try:
        plan = json.loads(raw)
    except json.JSONDecodeError as e:
        die(f"input is not valid JSON: {e}")
    if not isinstance(plan, dict) or "format_version" not in plan:
        die("no format_version key: this is not output of `terraform show -json`")
    if "values" in plan and "planned_values" not in plan and "resource_changes" not in plan:
        die("this looks like a state file (`terraform show -json` with no plan file), not a plan")
    if "planned_values" not in plan and "resource_changes" not in plan:
        die("no planned_values or resource_changes: this is not a plan")
    rc = plan.get("resource_changes", [])
    if not isinstance(rc, list):
        die("resource_changes is not a list")
    return plan


def kind(actions):
    a = list(actions or [])
    if a == ["delete", "create"]:
        return "replace (destroy then create)"
    if a == ["create", "delete"]:
        return "replace (create then destroy)"
    if len(a) == 1:
        return {"create": "create", "update": "update", "delete": "delete", "read": "read",
                "no-op": "no-op", "forget": "forget"}.get(a[0], a[0])
    return "+".join(a) or "unknown"


def fmt_path(path):
    out = ""
    for step in path:
        if isinstance(step, int):
            out += f"[{step}]"
        else:
            out += ("." if out else "") + str(step)
    return out or "(root)"


def changed_keys(change):
    """Top-level attribute names whose value differs or becomes unknown. Names only, no values."""
    before = change.get("before") or {}
    after = change.get("after") or {}
    unknown = change.get("after_unknown") or {}
    if not isinstance(before, dict) or not isinstance(after, dict):
        return []
    keys = set(before) | set(after) | (set(unknown) if isinstance(unknown, dict) else set())
    out = []
    for k in sorted(keys):
        if isinstance(unknown, dict) and unknown.get(k) is True and k not in before:
            continue  # computed attribute appearing on create
        if before.get(k) != after.get(k) or (isinstance(unknown, dict) and unknown.get(k)):
            out.append(k)
    return out


def walk_strings(value):
    """Every string in a resource body, skipping egress blocks (open egress is normal)."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for k, v in value.items():
            if k == "egress":
                continue
            for s in walk_strings(v):
                yield s
    elif isinstance(value, list):
        for v in value:
            for s in walk_strings(v):
                yield s


def as_list(v):
    return v if isinstance(v, list) else [v]


def broad_grants(value, rtype=""):
    """Set of broad-access markers found in a resource body: open ingress CIDRs and wildcard policy statements."""
    found = set()
    egress_rule = "egress" in rtype or (isinstance(value, dict) and value.get("type") == "egress")
    for s in walk_strings(value):
        for cidr in OPEN_CIDRS:
            if s == cidr and not egress_rule:
                found.add(f"open CIDR {cidr}")
        if '"Statement"' in s or "'Statement'" in s:
            try:
                doc = json.loads(s)
            except ValueError:
                continue
            for st in as_list(doc.get("Statement", [])) if isinstance(doc, dict) else []:
                if not isinstance(st, dict) or st.get("Effect") != "Allow":
                    continue
                actions = [a for a in as_list(st.get("Action", [])) if isinstance(a, str)]
                if any(a == "*" or a.endswith(":*") for a in actions):
                    found.add("policy allows wildcard action " +
                              ", ".join(sorted(a for a in actions if a == "*" or a.endswith(":*"))))
                if "*" in as_list(st.get("Resource", [])) and actions:
                    found.add("policy allows Resource \"*\"")
                principal = st.get("Principal")
                if principal == "*" or (isinstance(principal, dict) and
                                        "*" in as_list(principal.get("AWS", []))):
                    found.add("policy allows Principal \"*\"")
    return found


def is_stateful(rtype):
    return any(rtype.startswith(p) if p.endswith("_") else rtype == p for p in STATEFUL_PATTERNS)


def is_access(rtype):
    return any(p in rtype for p in ACCESS_PATTERNS)


def in_scope(address, scopes):
    if not scopes:
        return True
    for s in scopes:
        if address == s or address.startswith(s + ".") or address.startswith(s + "["):
            return True
    return False


def analyse(plan, scopes):
    counts = {}
    flagged = []
    for rc in plan.get("resource_changes", []):
        if not isinstance(rc, dict):
            continue
        change = rc.get("change") or {}
        actions = change.get("actions") or []
        k = kind(actions)
        counts[k] = counts.get(k, 0) + 1
        if k in ("no-op", "read"):
            continue
        addr = rc.get("address", "?")
        if rc.get("deposed"):
            addr += f" (deposed object {rc['deposed']})"
        rtype = rc.get("type", "")
        reasons = []
        severity = 0  # 1 care, 2 do-not-apply floor
        destructive = "delete" in actions
        if destructive:
            what = "replaced" if "create" in actions else "destroyed"
            line = f"will be {what}"
            paths = change.get("replace_paths") or []
            if paths:
                line += "; replacement forced by: " + ", ".join(fmt_path(p) for p in paths)
            if rc.get("action_reason"):
                line += f" (action_reason: {rc['action_reason']})"
            reasons.append(line)
            severity = max(severity, 1)
        if is_stateful(rtype):
            if destructive:
                reasons.append("stateful resource: data is lost unless a backup or snapshot exists")
                severity = 2
            elif k == "update":
                reasons.append("stateful resource changed in place")
                severity = max(severity, 1)
        before = change.get("before") or {}
        after = change.get("after") or {}
        if isinstance(before, dict) and isinstance(after, dict):
            for flag in PROTECTION_FLAGS:
                if before.get(flag) is True and after.get(flag) is False:
                    reasons.append(f"{flag} turned off")
                    severity = max(severity, 1)
            for flag in PUBLIC_BLOCK_FLAGS:
                if before.get(flag) is True and after.get(flag) is False:
                    reasons.append(f"access widened: {flag} turned off")
                    severity = 2
        if "create" in actions or k == "update":
            new = broad_grants(after, rtype) - broad_grants(before, rtype)
            if new:
                reasons.append("access widened: " + "; ".join(sorted(new)))
                public = any("open CIDR" in n or "Principal" in n for n in new)
                admin = any("wildcard action" in n for n in new) and any("Resource" in n for n in new)
                severity = 2 if (public or admin) else max(severity, 1)
            elif is_access(rtype) and not any("access widened" in r for r in reasons):
                reasons.append("access-control resource changed: read the before/after")
                severity = max(severity, 1)
        if change.get("importing"):
            reasons.append("import: Terraform will take over an existing object")
            severity = max(severity, 1)
        if k == "forget":
            reasons.append("forget: removed from state, the real object is left running")
            severity = max(severity, 1)
        if not in_scope(rc.get("address", ""), scopes):
            reasons.append("outside the stated scope")
            severity = max(severity, 1)
        if k == "update" and not reasons:
            continue
        if k == "create" and not reasons:
            continue
        flagged.append({
            "address": addr, "type": rtype, "action": k, "severity": severity,
            "reasons": reasons,
            "changed_attributes": changed_keys(change) if k == "update" else [],
        })

    drift = []
    for rd in plan.get("resource_drift", []) or []:
        if not isinstance(rd, dict):
            continue
        ch = rd.get("change") or {}
        drift.append({"address": rd.get("address", "?"), "action": kind(ch.get("actions")),
                      "changed_attributes": changed_keys(ch)})

    floor = "SAFE TO APPLY"
    if flagged or drift:
        floor = "APPLY WITH CARE"
    if any(f["severity"] == 2 for f in flagged):
        floor = "DO NOT APPLY"
    if plan.get("errored") is True:
        floor = "DO NOT APPLY"
    flagged.sort(key=lambda f: (-f["severity"], f["address"]))
    return {
        "terraform_version": plan.get("terraform_version", "unknown"),
        "format_version": plan.get("format_version"),
        "errored": plan.get("errored") is True,
        "counts": counts, "flagged": flagged, "drift": drift,
        "scope": scopes, "floor_verdict": floor,
    }


SEV = {2: "DO NOT APPLY", 1: "CARE", 0: "NOTE"}


def to_markdown(r):
    c = r["counts"]
    replace = c.get("replace (destroy then create)", 0) + c.get("replace (create then destroy)", 0)
    lines = [
        "# Terraform plan summary", "",
        f"Terraform {r['terraform_version']}, JSON format {r['format_version']}.", "",
        f"**Floor verdict: {r['floor_verdict']}** (mechanical; the reviewer reads every flagged change)", "",
        "| create | update | replace | destroy | read | forget | no-op |",
        "|---|---|---|---|---|---|---|",
        f"| {c.get('create', 0)} | {c.get('update', 0)} | {replace} | {c.get('delete', 0)} | "
        f"{c.get('read', 0)} | {c.get('forget', 0)} | {c.get('no-op', 0)} |", "",
    ]
    if r["errored"]:
        lines += ["The plan errored (errored: true). It is incomplete; do not apply it.", ""]
    lines += [f"Scope: {', '.join(r['scope'])}" if r["scope"] else "Scope: not given (no out-of-scope check)", ""]
    lines += ["## Changes to review", ""]
    if not r["flagged"]:
        lines += ["None flagged.", ""]
    for f in r["flagged"]:
        lines.append(f"- [{SEV[f['severity']]}] `{f['address']}` ({f['action']})")
        for reason in f["reasons"]:
            lines.append(f"  - {reason}")
        if f["changed_attributes"]:
            lines.append("  - changed attributes: " + ", ".join(f["changed_attributes"]))
    lines += ["", "## Drift (changed outside Terraform)", ""]
    if not r["drift"]:
        lines += ["None reported in resource_drift."]
    for d in r["drift"]:
        attrs = ", ".join(d["changed_attributes"]) or "no attribute detail"
        lines.append(f"- `{d['address']}` ({d['action']}): {attrs}")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("plan", help="path to `terraform show -json` output, or - for stdin")
    ap.add_argument("--scope", action="append", default=[],
                    help="address prefix the change is meant to touch (repeatable), e.g. module.api")
    ap.add_argument("--format", choices=("md", "json"), default="md")
    ap.add_argument("-o", "--out", help="write here instead of stdout")
    args = ap.parse_args()
    result = analyse(load_plan(args.plan), args.scope)
    text = to_markdown(result) if args.format == "md" else json.dumps(result, indent=2) + "\n"
    if args.out:
        try:
            with open(args.out, "w", encoding="utf-8") as fh:
                fh.write(text)
        except OSError as e:
            die(f"cannot write {args.out}: {e.strerror}")
        print(f"wrote {args.out}", file=sys.stderr)
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
