#!/usr/bin/env python3
"""Unit-economics sanity check for a lean canvas.

Stdlib only; runs on Python 3.9+. Computes, never estimates:

  * contribution (gross margin) per customer per period, and as a % of price;
  * customer lifetime in periods (given directly, or 1 / churn);
  * lifetime gross margin (LTV) and LTV:CAC;
  * CAC payback in periods, and whether it is longer than the lifetime;
  * the most a customer can cost to acquire: at break-even (LTV) and at 3:1 (LTV / 3);
  * break-even customers for the fixed costs, and the customers a stated
    market can supply, when those are given.

All money figures share one currency and one period (default "month"). Convert
an annual price to monthly before passing it, or pass --period year with
annual figures throughout.

Usage:
  python3 unit_economics.py --price 29 --variable-cost 6 --cac 400 \
      --lifetime 9 --fixed 4300
  python3 unit_economics.py --price 29 --variable-cost 6 --cac 400 --churn 0.11
  python3 unit_economics.py --json inputs.json [-o out.md]
  echo '{"price": 29, "variable_cost": 6, "cac": 400, "lifetime": 9}' | \
      python3 unit_economics.py --json -

JSON keys mirror the flags: price, variable_cost, cac, lifetime, churn,
fixed, market_customers, period. Flags given on the command line override
the JSON.

Exit codes: 0 ok, 2 bad input.
"""

from __future__ import annotations

import argparse
import json
import sys

KEYS = ("price", "variable_cost", "cac", "lifetime", "churn", "fixed", "market_customers")


def fail(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(2)


def load_json(path: str) -> dict:
    try:
        if path == "-":
            data = json.load(sys.stdin)
        else:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
    except FileNotFoundError:
        fail(f"no such file: {path}")
    except json.JSONDecodeError as exc:
        fail(f"not valid JSON ({exc})")
    if not isinstance(data, dict):
        fail("JSON input must be one object")
    return data


def number(name: str, value, minimum: float = 0.0, allow_equal: bool = True):
    if value is None:
        return None
    try:
        val = float(value)
    except (TypeError, ValueError):
        fail(f"{name} must be a number, got {value!r}")
    if val < minimum or (not allow_equal and val == minimum):
        op = ">=" if allow_equal else ">"
        fail(f"{name} must be {op} {minimum:g}, got {val:g}")
    return val


def money(x: float) -> str:
    return f"{x:,.2f}"


def compute(inp: dict) -> tuple[list[str], list[str]]:
    period = str(inp.get("period") or "month")
    price = number("price", inp.get("price"), 0.0, allow_equal=False)
    if price is None:
        fail("price is required (per customer per period)")
    vcost = number("variable_cost", inp.get("variable_cost")) or 0.0
    cac = number("cac", inp.get("cac"))
    lifetime = number("lifetime", inp.get("lifetime"), 0.0, allow_equal=False)
    churn = inp.get("churn")
    fixed = number("fixed", inp.get("fixed"))
    market = number("market_customers", inp.get("market_customers"))

    if churn is not None:
        churn = number("churn", churn, 0.0, allow_equal=False)
        if churn > 1:
            if churn <= 100:
                churn = churn / 100.0  # "11" meaning 11%
            else:
                fail("churn must be a fraction (0.11) or a percent (11)")
        if lifetime is None:
            lifetime = 1.0 / churn

    lines: list[str] = []
    flags: list[str] = []

    margin = price - vcost
    margin_pct = margin / price * 100
    lines.append(f"Price per customer per {period}: {money(price)}")
    if inp.get("variable_cost") is None:
        lines.append(f"Variable cost per customer per {period}: not given, treated as 0")
        flags.append("No cost to serve was given, so every margin figure here is an upper bound.")
    else:
        lines.append(f"Variable cost per customer per {period}: {money(vcost)}")
    lines.append(f"Contribution per customer per {period}: {money(margin)} ({margin_pct:.1f}% gross margin)")
    if margin <= 0:
        flags.append(f"Each customer costs more to serve than they pay ({money(margin)} per {period}). No volume fixes this.")

    ltv = None
    if lifetime is not None:
        src = f"1 / churn of {churn * 100:.1f}%" if churn is not None and inp.get("lifetime") is None else "as given"
        lines.append(f"Customer lifetime: {lifetime:.1f} {period}s ({src})")
        ltv = margin * lifetime
        lines.append(f"Lifetime contribution (LTV): {money(ltv)}")

    if cac is not None:
        lines.append(f"Customer acquisition cost (CAC): {money(cac)}")
        if margin > 0:
            payback = cac / margin
            lines.append(f"CAC payback: {payback:.1f} {period}s")
            if lifetime is not None and payback > lifetime:
                flags.append(
                    f"CAC payback ({payback:.1f} {period}s) is longer than the customer lifetime "
                    f"({lifetime:.1f} {period}s): every acquired customer loses {money(cac - ltv)}."
                )
        if ltv is not None:
            ratio = ltv / cac if cac > 0 else float("inf")
            lines.append(f"LTV:CAC: {ratio:.2f}" if cac > 0 else "LTV:CAC: no acquisition cost given as 0")
            if cac > 0 and ratio < 1:
                flags.append(f"LTV:CAC is {ratio:.2f}: acquisition destroys money before fixed costs.")
            elif cac > 0 and ratio < 3:
                flags.append(f"LTV:CAC is {ratio:.2f}, under the 3:1 most subscription businesses need to cover fixed costs.")

    if ltv is not None and ltv > 0:
        lines.append(f"Most a customer can cost to acquire: {money(ltv)} at break-even, {money(ltv / 3)} at 3:1")

    if fixed is not None:
        lines.append(f"Fixed costs per {period}: {money(fixed)}")
        if margin > 0:
            be = fixed / margin
            be_whole = int(be) if be == int(be) else int(be) + 1
            lines.append(f"Break-even customers (active at once): {be_whole:,}")
            if market is not None:
                lines.append(f"Customers the stated market holds: {int(market):,}")
                if be_whole > market:
                    flags.append(
                        f"Break-even needs {be_whole:,} active customers but the stated market holds {int(market):,}."
                    )
                else:
                    share = be_whole / market * 100 if market else 0.0  # 0 needed of a 0 market
                    lines.append(f"Break-even share of the stated market: {share:.1f}%")
                    if share >= 25:
                        flags.append(
                            f"Break-even needs {share:.0f}% of the stated market as paying customers at the same time."
                        )
            if cac is not None and ltv is not None and ltv <= cac:
                flags.append("Break-even customers cannot be reached through paid acquisition at this CAC: each one adds a loss.")

    missing = [k for k in ("variable_cost", "cac", "lifetime/churn", "fixed")
               if (k == "lifetime/churn" and lifetime is None)
               or (k != "lifetime/churn" and inp.get(k) is None)]
    if missing:
        lines.append("Not computed (input missing): " + ", ".join(missing))
    return lines, flags


def main() -> None:
    ap = argparse.ArgumentParser(description="Unit-economics sanity check for a lean canvas.")
    ap.add_argument("--json", metavar="PATH", help="JSON object of inputs, or - for stdin")
    ap.add_argument("--price", help="price per customer per period")
    ap.add_argument("--variable-cost", dest="variable_cost", help="cost to serve one customer per period")
    ap.add_argument("--cac", help="cost to acquire one paying customer")
    ap.add_argument("--lifetime", help="average customer lifetime in periods")
    ap.add_argument("--churn", help="churn per period, as 0.11 or 11")
    ap.add_argument("--fixed", help="fixed costs per period")
    ap.add_argument("--market-customers", dest="market_customers", help="customers the stated market holds")
    ap.add_argument("--period", help='period label, default "month"')
    ap.add_argument("-o", "--output", help="write the report to this path instead of stdout")
    args = ap.parse_args()

    inp: dict = load_json(args.json) if args.json else {}
    unknown = set(inp) - set(KEYS) - {"period"}
    if unknown:
        fail("unknown JSON keys: " + ", ".join(sorted(unknown)))
    for key in KEYS + ("period",):
        val = getattr(args, key)
        if val is not None:
            inp[key] = val

    lines, flags = compute(inp)
    out = ["Unit economics", ""] + [f"- {ln}" for ln in lines]
    out += ["", "Where the numbers don't close:" if flags else "Where the numbers don't close: none found."]
    out += [f"- {f}" for f in flags]
    text = "\n".join(out) + "\n"
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(text)
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
