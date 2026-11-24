#!/usr/bin/env python3
"""RCM Denial Management Analytics.

Load a denial worklist CSV, compute denial KPIs (rate, dollars at risk,
breakdowns by payer / reason / category, appeal success, monthly trend),
print a management summary, optionally export JSON and draft appeal letters.

Usage:
    python denial_analytics.py data/sample_denials.csv
    python denial_analytics.py data/sample_denials.csv --json report.json
    python denial_analytics.py data/sample_denials.csv --appeals appeals_out/
"""

import argparse
import csv
import json
import os
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass

from denial_codes import describe_carc
from appeal_templates import generate_appeal

EXPECTED_COLUMNS = [
    "denial_id", "claim_id", "date_of_service", "denial_date", "payer",
    "cpt_code", "icd10_code", "billed_amount", "carc_code", "rarc_code",
    "category", "appeal_filed", "appeal_outcome", "resolved_amount",
]


@dataclass
class Denial:
    denial_id: str
    claim_id: str
    date_of_service: str
    denial_date: str
    payer: str
    cpt_code: str
    icd10_code: str
    billed_amount: float
    carc_code: str
    rarc_code: str
    category: str
    appeal_filed: bool
    appeal_outcome: str  # "", "won", "lost", "pending"
    resolved_amount: float


def load_denials(path):
    """Load a denial worklist CSV into a list of Denial records."""
    denials = []
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        missing = [c for c in ("denial_id", "claim_id", "payer", "billed_amount", "carc_code")
                   if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"CSV is missing required columns: {', '.join(missing)}")
        for i, row in enumerate(reader, start=2):
            try:
                denials.append(Denial(
                    denial_id=row["denial_id"].strip(),
                    claim_id=row["claim_id"].strip(),
                    date_of_service=row.get("date_of_service", "").strip(),
                    denial_date=row.get("denial_date", "").strip(),
                    payer=row["payer"].strip(),
                    cpt_code=row.get("cpt_code", "").strip(),
                    icd10_code=row.get("icd10_code", "").strip(),
                    billed_amount=float(row["billed_amount"] or 0),
                    carc_code=row["carc_code"].strip(),
                    rarc_code=row.get("rarc_code", "").strip(),
                    category=row.get("category", "").strip() or describe_carc(row["carc_code"].strip())[1],
                    appeal_filed=row.get("appeal_filed", "").strip().lower() in ("yes", "true", "1"),
                    appeal_outcome=row.get("appeal_outcome", "").strip().lower(),
                    resolved_amount=float(row.get("resolved_amount") or 0),
                ))
            except (ValueError, KeyError) as exc:
                raise ValueError(f"Row {i}: bad data ({exc})") from exc
    return denials


def _dollars(rows):
    return round(sum(d.billed_amount for d in rows), 2)


def summarize(denials, total_claims=None):
    """Compute the headline KPIs for a denial worklist.

    total_claims: total claims submitted in the period (for denial-rate %).
    If omitted, the denial rate is reported against the worklist size only.
    """
    if not denials:
        return {"denial_count": 0}

    by_payer = defaultdict(list)
    by_carc = defaultdict(list)
    by_category = defaultdict(list)
    by_month = defaultdict(list)
    for d in denials:
        by_payer[d.payer].append(d)
        by_carc[d.carc_code].append(d)
        by_category[d.category].append(d)
        month = (d.denial_date or "unknown")[:7]
        by_month[month].append(d)

    appealed = [d for d in denials if d.appeal_filed]
    won = [d for d in appealed if d.appeal_outcome == "won"]
    lost = [d for d in appealed if d.appeal_outcome == "lost"]

    def top(mapping, n=10):
        return sorted(
            ({"key": k, "count": len(v), "billed_amount": _dollars(v)}
             for k, v in mapping.items()),
            key=lambda r: (-r["billed_amount"], -r["count"]),
        )[:n]

    return {
        "denial_count": len(denials),
        "total_billed_at_risk": _dollars(denials),
        "denial_rate_pct": (round(100 * len(denials) / total_claims, 1)
                            if total_claims else None),
        "by_payer": top(by_payer),
        "by_reason_code": [
            {**r, "description": describe_carc(r["key"])[0],
             "appealable": describe_carc(r["key"])[2]}
            for r in top(by_carc)
        ],
        "by_category": top(by_category),
        "monthly_trend": [
            {"month": m, "count": len(v), "billed_amount": _dollars(v)}
            for m, v in sorted(by_month.items())
        ],
        "appeals": {
            "filed": len(appealed),
            "won": len(won),
            "lost": len(lost),
            "pending": len(appealed) - len(won) - len(lost),
            "win_rate_pct": (round(100 * len(won) / (len(won) + len(lost)), 1)
                             if (won or lost) else None),
            "recovered_amount": _dollars(won) if won else 0.0,
        },
    }


def print_report(summary, denials):
    """Render the management summary to stdout."""
    if summary.get("denial_count", 0) == 0:
        print("No denials in the worklist.")
        return

    print("=" * 64)
    print("RCM DENIAL ANALYTICS - MANAGEMENT SUMMARY")
    print("=" * 64)
    print(f"Open/analyzed denials : {summary['denial_count']}")
    print(f"Billed $ at risk      : ${summary['total_billed_at_risk']:,.2f}")
    if summary.get("denial_rate_pct") is not None:
        print(f"Denial rate           : {summary['denial_rate_pct']}% of submitted claims")

    def section(title, rows, extra=None):
        print(f"\n-- {title} " + "-" * max(2, 58 - len(title)))
        for r in rows:
            line = f"  {r['key']:<28} {r['count']:>4} denials   ${r['billed_amount']:>12,.2f}"
            if extra:
                line += extra(r)
            print(line)

    section("Top payers by denied dollars", summary["by_payer"][:5])
    section("Top categories", summary["by_category"][:5])
    print("\n-- Top reason codes (CARC) " + "-" * 36)
    for r in summary["by_reason_code"][:6]:
        flag = "" if r["appealable"] else "  [not appealable]"
        print(f"  CARC {r['key']:<5} {r['description'][:38]:<40} "
              f"{r['count']:>3}x  ${r['billed_amount']:>10,.2f}{flag}")

    print("\n-- Monthly trend " + "-" * 46)
    for r in summary["monthly_trend"]:
        print(f"  {r['month']:<10} {r['count']:>4} denials   ${r['billed_amount']:>12,.2f}")

    a = summary["appeals"]
    print("\n-- Appeals " + "-" * 53)
    print(f"  Filed: {a['filed']}   Won: {a['won']}   Lost: {a['lost']}   Pending: {a['pending']}")
    if a["win_rate_pct"] is not None:
        print(f"  Win rate: {a['win_rate_pct']}%   Recovered: ${a['recovered_amount']:,.2f}")
    unappealed = sum(1 for d in denials if not d.appeal_filed)
    if unappealed:
        print(f"  Not yet appealed: {unappealed} (run with --appeals to draft letters)")


def write_appeals(denials, out_dir, provider_name):
    """Draft one appeal letter per un-appealed, appealable denial."""
    os.makedirs(out_dir, exist_ok=True)
    written = 0
    for d in denials:
        if d.appeal_filed:
            continue
        if not describe_carc(d.carc_code)[2]:
            continue
        letter = generate_appeal(d, provider_name=provider_name)
        path = os.path.join(out_dir, f"appeal_{d.denial_id}.txt")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(letter)
        written += 1
    return written


def main(argv=None):
    parser = argparse.ArgumentParser(description="RCM denial worklist analytics")
    parser.add_argument("csv", help="Path to the denial worklist CSV")
    parser.add_argument("--total-claims", type=int, default=None,
                        help="Total claims submitted in the period (enables denial-rate %)")
    parser.add_argument("--json", metavar="OUT.json", help="Export the summary as JSON")
    parser.add_argument("--appeals", metavar="OUT_DIR",
                        help="Draft appeal letters for un-appealed, appealable denials")
    parser.add_argument("--provider", default="ABC Medical Group",
                        help="Provider name used in appeal letters")
    args = parser.parse_args(argv)

    try:
        denials = load_denials(args.csv)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    summary = summarize(denials, total_claims=args.total_claims)
    print_report(summary, denials)

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(summary, fh, indent=2)
        print(f"\nJSON summary written to {args.json}")

    if args.appeals:
        n = write_appeals(denials, args.appeals, args.provider)
        print(f"Drafted {n} appeal letter(s) into {args.appeals}/")

    return 0


if __name__ == "__main__":
    sys.exit(main())
