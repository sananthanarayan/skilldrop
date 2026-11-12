#!/usr/bin/env python3
"""Model a startup's ownership through SAFEs, convertible notes and a priced round. Stdlib only.

Reads a cap.json: the shareholders, the option pool, every SAFE and convertible note, and
(optionally) the priced round's pre-money valuation, new money and target option pool. Prints:
  - the fully diluted cap table today, and what the SAFEs already promise at their caps
  - each SAFE's and note's conversion price, and whether its cap or its discount applied
  - the price per share, the option pool top-up, and the cap table after the round
  - founder ownership at other pre-money valuations (--scenarios)
and checks that the post-money valuation equals price per share × fully diluted shares and
that ownership sums to 100 %.

Conventions (printed with every result, because term sheets differ):
  - post-money SAFE (YC 2018+): capitalization for its cap price includes every share,
    option, the existing unissued pool and all converting securities, but not the pool
    increase made in the round
  - pre-money SAFE and convertible note: cap price = cap ÷ (existing fully diluted shares +
    the pool increase), excluding converting securities
  - the pool top-up is in the pre-money ("option pool shuffle"): the unissued pool after the
    round is the target share of post-money fully diluted shares
  - note interest is simple, from its issue date to the closing date; shares round down

Usage:
  python3 cap_table.py cap.json [--scenarios 8000000,12000000] [--csv after.csv] [--json]
Exit codes: 0 computed, 1 a check failed or the round cannot be modelled, 2 bad input.
"""
import argparse
import csv
import datetime as dt
import json
import math
import sys


class InputError(Exception):
    pass


def num(v, what, lo=0.0, allow_none=False):
    if v is None and allow_none:
        return None
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v < lo:
        raise InputError(f"{what} must be a number of at least {lo:g}")
    return float(v)


def frac(v, what):
    """A rate given as 0.2 or 20 (meaning 20 %)."""
    if v is None:
        return 0.0
    v = num(v, what)
    if v >= 1:
        v /= 100
    if v >= 1:
        raise InputError(f"{what} must be under 100 %")
    return v


def date(v, what):
    if v is None:
        return None
    try:
        return dt.date.fromisoformat(str(v))
    except ValueError:
        raise InputError(f"{what} must be a date as YYYY-MM-DD")


def load(data):
    if not isinstance(data, dict):
        raise InputError("cap.json must be a JSON object")
    holders = []
    for i, h in enumerate(data.get("holders") or [], 1):
        if not isinstance(h, dict) or not str(h.get("name", "")).strip():
            raise InputError(f"holder {i} needs a `name`")
        holders.append({"name": str(h["name"]).strip(), "class": str(h.get("class", "common")),
                        "shares": num(h.get("shares"), f"{h['name']}: shares")})
    if not holders:
        raise InputError("`holders` must list at least one shareholder with shares")
    opts = data.get("options") or {}
    if not isinstance(opts, dict):
        raise InputError("`options` must be an object with `granted` and `pool_unissued`")
    granted = num(opts.get("granted", 0), "options.granted")
    unissued = num(opts.get("pool_unissued", 0), "options.pool_unissued")
    convs = []
    for kind, key in (("safe", "safes"), ("note", "notes")):
        for i, s in enumerate(data.get(key) or [], 1):
            if not isinstance(s, dict) or not str(s.get("holder", "")).strip():
                raise InputError(f"{kind} {i} needs a `holder`")
            name = str(s["holder"]).strip()
            c = {"kind": kind, "holder": name,
                 "cap": num(s.get("cap"), f"{name}: cap", 1, allow_none=True),
                 "discount": frac(s.get("discount"), f"{name}: discount"),
                 "mfn": bool(s.get("mfn", False))}
            if kind == "safe":
                c["amount"] = num(s.get("amount"), f"{name}: amount", 1)
                basis = str(s.get("type", "post")).lower()
                if basis not in ("post", "pre"):
                    raise InputError(f"{name}: SAFE type must be \"post\" or \"pre\"")
                c["basis"] = basis
            else:
                c["principal"] = num(s.get("principal"), f"{name}: principal", 1)
                c["rate"] = frac(s.get("rate"), f"{name}: rate")
                c["issued"] = date(s.get("issued"), f"{name}: issued")
                c["basis"] = "pre"
            convs.append(c)
    rnd = data.get("round")
    if rnd is not None:
        if not isinstance(rnd, dict):
            raise InputError("`round` must be an object")
        inv = []
        for i, x in enumerate(rnd.get("investors") or [], 1):
            if not isinstance(x, dict) or not str(x.get("name", "")).strip():
                raise InputError(f"round investor {i} needs a `name`")
            inv.append({"name": str(x["name"]).strip(), "amount": num(x.get("amount"), f"{x['name']}: amount", 1)})
        if not inv:
            raise InputError("`round.investors` must list who puts in the new money")
        pool_in = str(rnd.get("pool_in", "pre")).lower()
        if pool_in not in ("pre", "post"):
            raise InputError("round.pool_in must be \"pre\" (top-up in the pre-money, the usual term) or \"post\"")
        rnd = {"pre_money": num(rnd.get("pre_money"), "round.pre_money", 1),
               "investors": inv, "pool_target": frac(rnd.get("pool_target"), "round.pool_target"),
               "pool_in": pool_in, "close": date(rnd.get("close"), "round.close")}
    return {"company": str(data.get("company", "The company")), "currency": str(data.get("currency", "USD")),
            "holders": holders, "granted": granted, "unissued": unissued, "convs": convs, "round": rnd}


def note_amount(c, close, warns):
    if c["kind"] != "note":
        return c["amount"]
    if c["rate"] and (c["issued"] is None or close is None):
        warns.append(f"{c['holder']}: note interest not counted; give `issued` and the round's `close` date")
        return c["principal"]
    years = max(0.0, (close - c["issued"]).days / 365) if c["issued"] and close else 0.0
    return c["principal"] * (1 + c["rate"] * years)


def today_fd(cap):
    return sum(h["shares"] for h in cap["holders"]) + cap["granted"] + cap["unissued"]


def model(cap, pre_money=None):
    """Solve the round. Returns None when there is no round to model."""
    rnd = cap["round"]
    if rnd is None:
        return None
    pre = pre_money if pre_money is not None else rnd["pre_money"]
    warns = []
    base = today_fd(cap)
    amounts = [note_amount(c, rnd["close"], warns) for c in cap["convs"]]
    new_money = sum(x["amount"] for x in rnd["investors"])
    conv_shares = [0.0] * len(cap["convs"])
    pool_inc = 0.0
    price = pre / base
    in_pre = rnd["pool_in"] == "pre"
    for _ in range(500):
        conv_total = sum(conv_shares)
        pre_fd = base + conv_total + (pool_inc if in_pre else 0)
        price = pre / pre_fd
        new = []
        how = []
        for c, amt in zip(cap["convs"], amounts):
            cands = {"round price": price}
            if c["discount"]:
                cands["discount"] = price * (1 - c["discount"])
            if c["cap"]:
                denom = base + conv_total if c["basis"] == "post" else base + pool_inc
                cands["cap"] = c["cap"] / denom
            pick = min(cands, key=cands.get)
            new.append(amt / cands[pick])
            how.append((pick, cands[pick]))
        post_fd = pre_fd + new_money / price + (0 if in_pre else pool_inc)
        new_pool = max(0.0, rnd["pool_target"] * post_fd - cap["unissued"])
        delta = max(abs(a - b) for a, b in zip(new + [new_pool], conv_shares + [pool_inc])) if new else abs(new_pool - pool_inc)
        conv_shares, pool_inc = new, new_pool
        if delta < 1e-6:
            break
    else:
        return {"error": "the round does not settle: the SAFEs' caps leave no room for the new money at this valuation"}
    conv_total = sum(conv_shares)
    pre_fd = base + conv_total + (pool_inc if in_pre else 0)
    price = pre / pre_fd
    rows = [{"name": h["name"], "class": h["class"], "shares": h["shares"]} for h in cap["holders"]]
    convs = []
    for c, amt, sh, (pick, p) in zip(cap["convs"], amounts, conv_shares, how):
        shares = math.floor(sh + 1e-9)
        convs.append({"holder": c["holder"], "kind": c["kind"], "basis": c["basis"], "invested": amt,
                      "price": p, "by": pick, "shares": shares, "mfn": c["mfn"]})
        rows.append({"name": c["holder"], "class": f"preferred ({c['kind']})", "shares": shares})
    investors = []
    for x in rnd["investors"]:
        shares = math.floor(x["amount"] / price + 1e-9)
        investors.append({"name": x["name"], "amount": x["amount"], "shares": shares})
        rows.append({"name": x["name"], "class": "preferred (round)", "shares": shares})
    rows.append({"name": "Options granted", "class": "options", "shares": cap["granted"]})
    pool_after = math.floor(cap["unissued"] + pool_inc + 1e-9)
    rows.append({"name": "Option pool, unissued", "class": "options", "shares": pool_after})
    total = sum(r["shares"] for r in rows)
    for r in rows:
        r["pct"] = r["shares"] / total * 100
    post_val = price * total
    for c in cap["convs"]:
        if c["mfn"] and not c["cap"] and not c["discount"]:
            warns.append(f"{c['holder']}: an MFN SAFE with no terms of its own converts at the round price here; "
                         "check whether a later SAFE's cap or discount applies to it")
    fails = []
    if abs(sum(r["pct"] for r in rows) - 100) > 1e-6:
        fails.append("ownership does not sum to 100 %")
    expected = pre + new_money + (0 if in_pre else (pool_after - cap["unissued"]) * price)
    if abs(post_val - expected) / expected > 0.001:
        fails.append(f"post-money {post_val:,.0f} is not pre-money + new money {expected:,.0f}")
    return {"pre_money": pre, "new_money": new_money, "price": price, "pool_increase": pool_after - cap["unissued"],
            "pool_after": pool_after, "convs": convs, "investors": investors, "rows": rows, "total": total,
            "post_money": post_val, "pool_in": rnd["pool_in"],
            "effective_pre": pre - ((pool_after - cap["unissued"]) * price if in_pre else 0),
            "warns": warns, "fails": fails}


def stack(cap):
    """What the post-money SAFEs already promise: amount ÷ cap each, before any round."""
    out = []
    for c in cap["convs"]:
        if c["kind"] == "safe" and c["basis"] == "post" and c["cap"]:
            out.append((c["holder"], c["amount"], c["cap"], c["amount"] / c["cap"]))
    return out


def money(v, cur):
    sym = {"USD": "$", "EUR": "€", "GBP": "£", "INR": "₹"}.get(cur.upper(), "")
    return f"{sym}{v:,.0f}" if sym else f"{v:,.0f} {cur}"


def report(cap, r, scen):
    cur = cap["currency"]
    L = [f"# {cap['company']}: cap table", "", "## Today, fully diluted", "",
         "| Holder | Class | Shares | % |", "|---|---|---:|---:|"]
    base = today_fd(cap)
    for h in cap["holders"]:
        L.append(f"| {h['name']} | {h['class']} | {h['shares']:,.0f} | {h['shares'] / base * 100:.2f} |")
    L.append(f"| Options granted | options | {cap['granted']:,.0f} | {cap['granted'] / base * 100:.2f} |")
    L.append(f"| Option pool, unissued | options | {cap['unissued']:,.0f} | {cap['unissued'] / base * 100:.2f} |")
    L.append(f"| **Total** | | **{base:,.0f}** | **100.00** |")
    st = stack(cap)
    if st:
        L += ["", "Post-money SAFEs already promise, at their caps (amount ÷ cap):", ""]
        for name, amt, capv, share in st:
            L.append(f"- {name}: {money(amt, cur)} ÷ {money(capv, cur)} = {share * 100:.2f} %")
        tot = sum(s[3] for s in st)
        L.append(f"- **Together: {tot * 100:.2f} %** of the company before the round's new money and pool top-up")
    if r is None:
        L += ["", "No priced round given, so nothing converts yet."]
        return "\n".join(L) + "\n"
    if "error" in r:
        L += ["", f"FAIL {r['error']}"]
        return "\n".join(L) + "\n"
    L += ["", "## The round", "",
          f"- Pre-money valuation: {money(r['pre_money'], cur)}; new money: {money(r['new_money'], cur)}; "
          f"post-money: {money(r['post_money'], cur)}",
          f"- Price per share: {r['price']:.4f}",
          f"- Option pool top-up ({'in the pre-money' if r['pool_in'] == 'pre' else 'after the round, diluting the new investors too'}): "
          f"{r['pool_increase']:,.0f} shares, unissued pool after: {r['pool_after']:,.0f} "
          f"({r['pool_after'] / r['total'] * 100:.2f} % post-money)",
          f"- Effective pre-money for existing holders, after the pool top-up: {money(r['effective_pre'], cur)}"]
    if r["convs"]:
        L += ["", "| SAFE or note | Invested (with interest) | Converts at | By | Shares |", "|---|---:|---:|---|---:|"]
        for c in r["convs"]:
            L.append(f"| {c['holder']} ({c['basis']}-money {c['kind']}) | {money(c['invested'], cur)} | "
                     f"{c['price']:.4f} | {c['by']} | {c['shares']:,.0f} |")
    L += ["", "## After the round, fully diluted", "", "| Holder | Class | Shares | % |", "|---|---|---:|---:|"]
    for row in r["rows"]:
        L.append(f"| {row['name']} | {row['class']} | {row['shares']:,.0f} | {row['pct']:.2f} |")
    L.append(f"| **Total** | | **{r['total']:,.0f}** | **100.00** |")
    if scen:
        L += ["", "## At other pre-money valuations", "",
              "| Pre-money | Price per share | " + " | ".join(h["name"] for h in cap["holders"]) + " | New investors |",
              "|---:|---:|" + "---:|" * (len(cap["holders"]) + 1)]
        for v in scen:
            s = model(cap, v)
            if s is None or "error" in s:
                L.append(f"| {money(v, cur)} | cannot settle | " + " | " * len(cap["holders"]) + " |")
                continue
            pct = {row["name"]: row["pct"] for row in s["rows"]}
            inv = sum(pct[x["name"]] for x in s["investors"])
            L.append(f"| {money(v, cur)} | {s['price']:.4f} | " + " | ".join(f"{pct[h['name']]:.2f} %" for h in cap["holders"])
                     + f" | {inv:.2f} % |")
    L += ["", "Conventions: post-money SAFEs exclude the round's pool top-up from their cap price; pre-money SAFEs "
          "and notes divide their cap by existing shares plus the top-up; the top-up is in the pre-money; note "
          "interest is simple; shares round down."]
    for f in r["fails"]:
        L.append(f"FAIL {f}")
    for w in r["warns"]:
        L.append(f"WARN {w}")
    return "\n".join(L) + "\n"


def parse_scenarios(text):
    """'8m,12m', '8000000 12000000' or '8M;12.5M' -> [8e6, 12e6]."""
    out = []
    for tok in text.replace(";", " ").replace(",", " ").split():
        t = tok.strip().lower().lstrip("$€£₹")
        mult = {"k": 1e3, "m": 1e6, "b": 1e9}.get(t[-1:], 1)
        if mult != 1:
            t = t[:-1]
        try:
            out.append(num(float(t) * mult, "scenario", 1))
        except ValueError:
            raise InputError(f"scenario {tok!r} is not a valuation; write 8m or 8000000")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Model ownership through SAFEs, notes and a priced round.")
    ap.add_argument("cap")
    ap.add_argument("--scenarios", help="comma-separated pre-money valuations to compare")
    ap.add_argument("--csv", help="write the cap table after the round here")
    ap.add_argument("--json", action="store_true", help="print the figures as JSON")
    args = ap.parse_args(argv)
    try:
        with open(args.cap, encoding="utf-8-sig") as f:
            cap = load(json.load(f))
        scen = parse_scenarios(args.scenarios) if args.scenarios else []
    except (OSError, ValueError, UnicodeDecodeError) as e:
        print(f"FAIL cannot read input: {e}")
        return 2
    except InputError as e:
        print(f"FAIL {e}")
        return 2
    r = model(cap)
    if args.json:
        print(json.dumps({"today_fd": today_fd(cap), "safe_stack": stack(cap), "round": r}, indent=2, default=str))
    else:
        print(report(cap, r, scen), end="")
    if args.csv and r and "error" not in r:
        with open(args.csv, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["Holder", "Class", "Shares", "Percent"])
            for row in r["rows"]:
                w.writerow([row["name"], row["class"], int(row["shares"]), f"{row['pct']:.4f}"])
    if r and ("error" in r or r["fails"]):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
