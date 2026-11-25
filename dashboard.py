#!/usr/bin/env python3
"""Generate a polished, self-contained HTML dashboard from a denial summary.

Usage:
    python denial_analytics.py data/sample_denials.csv --json report.json
    python dashboard.py report.json -o dashboard.html
Then open dashboard.html in any browser. No dependencies, no internet needed.
"""

import argparse
import html
import json
from datetime import date

CSS = """
:root { --bg:#0d1117; --card:#161b22; --border:#30363d; --text:#e6edf3;
        --muted:#8b949e; --accent:#2f81f7; --good:#3fb950; --warn:#d29922; --bad:#f85149; }
* { box-sizing:border-box; margin:0; padding:0; }
body { background:var(--bg); color:var(--text); font-family:-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif; padding:32px; }
.wrap { max-width:1100px; margin:0 auto; }
header { display:flex; justify-content:space-between; align-items:baseline; border-bottom:1px solid var(--border); padding-bottom:16px; margin-bottom:24px; }
h1 { font-size:24px; } h1 span { color:var(--accent); }
.date { color:var(--muted); font-size:13px; }
.cards { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:14px; margin-bottom:28px; }
.card { background:var(--card); border:1px solid var(--border); border-radius:10px; padding:18px; }
.card .label { color:var(--muted); font-size:12px; text-transform:uppercase; letter-spacing:.5px; }
.card .value { font-size:28px; font-weight:700; margin-top:6px; }
.card .sub { color:var(--muted); font-size:12px; margin-top:4px; }
.good { color:var(--good); } .bad { color:var(--bad); } .warn { color:var(--warn); }
section { background:var(--card); border:1px solid var(--border); border-radius:10px; padding:20px; margin-bottom:20px; }
h2 { font-size:16px; margin-bottom:16px; }
.bar-row { display:grid; grid-template-columns:170px 1fr 110px; align-items:center; gap:12px; margin-bottom:10px; font-size:13px; }
.bar-row .name { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.bar-track { background:#21262d; border-radius:5px; height:20px; overflow:hidden; }
.bar-fill { background:var(--accent); height:100%; border-radius:5px; }
.bar-row .amt { text-align:right; color:var(--muted); }
table { width:100%; border-collapse:collapse; font-size:13px; }
th { text-align:left; color:var(--muted); font-weight:600; padding:8px 10px; border-bottom:1px solid var(--border); }
td { padding:8px 10px; border-bottom:1px solid #21262d; }
tr:last-child td { border-bottom:none; }
.tag { display:inline-block; padding:2px 8px; border-radius:10px; font-size:11px; }
.tag.yes { background:rgba(63,185,80,.15); color:var(--good); }
.tag.no { background:rgba(248,81,73,.15); color:var(--bad); }
.cols { display:grid; grid-template-columns:1fr 1fr; gap:20px; }
@media (max-width:800px){ .cols { grid-template-columns:1fr; } }
footer { color:var(--muted); font-size:12px; text-align:center; margin-top:24px; }
"""


def esc(s):
    return html.escape(str(s))


def money(v):
    return f"${v:,.2f}"


def bar_rows(rows, key_label="key"):
    if not rows:
        return "<p>No data.</p>"
    peak = max(r["billed_amount"] for r in rows) or 1
    out = []
    for r in rows:
        pct = max(2, round(100 * r["billed_amount"] / peak))
        out.append(
            f'<div class="bar-row"><div class="name">{esc(r[key_label])}</div>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{pct}%"></div></div>'
            f'<div class="amt">{r["count"]} &middot; {money(r["billed_amount"])}</div></div>'
        )
    return "\n".join(out)


def render(summary, generated=None):
    generated = generated or date.today().isoformat()
    n = summary.get("denial_count", 0)
    a = summary.get("appeals", {})

    cards = [
        ("Open denials", f"{n}", "", ""),
        ("Billed $ at risk", money(summary.get("total_billed_at_risk", 0)), "", "bad"),
    ]
    if summary.get("denial_rate_pct") is not None:
        cards.append(("Denial rate", f'{summary["denial_rate_pct"]}%', "of submitted claims", "warn"))
    if a:
        win = a.get("win_rate_pct")
        cards.append(("Appeal win rate", f"{win}%" if win is not None else "n/a",
                      f'{a.get("won", 0)} won / {a.get("lost", 0)} lost', "good"))
        cards.append(("Recovered", money(a.get("recovered_amount", 0)), "via appeals", "good"))

    cards_html = "\n".join(
        f'<div class="card"><div class="label">{esc(label)}</div>'
        f'<div class="value {cls}">{esc(value)}</div>'
        f'<div class="sub">{esc(sub)}</div></div>'
        for label, value, sub, cls in cards
    )

    carc_rows = "\n".join(
        f'<tr><td>CARC {esc(r["key"])}</td><td>{esc(r["description"])}</td>'
        f'<td>{r["count"]}</td><td>{money(r["billed_amount"])}</td>'
        f'<td><span class="tag {"yes" if r["appealable"] else "no"}">'
        f'{"appealable" if r["appealable"] else "not appealable"}</span></td></tr>'
        for r in summary.get("by_reason_code", [])
    )

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Codifyre AI - Denial Management Dashboard</title>
<style>{CSS}</style></head><body><div class="wrap">
<header><h1><span>Codifyre AI</span> &middot; Denial Management Dashboard</h1>
<div class="date">Generated {esc(generated)}</div></header>
<div class="cards">{cards_html}</div>
<div class="cols">
<section><h2>Top payers by denied dollars</h2>{bar_rows(summary.get("by_payer", [])[:6])}</section>
<section><h2>Denial categories</h2>{bar_rows(summary.get("by_category", [])[:6])}</section>
</div>
<section><h2>Monthly trend</h2>{bar_rows(summary.get("monthly_trend", []), key_label="month")}</section>
<section><h2>Reason codes (CARC)</h2>
<table><tr><th>Code</th><th>Description</th><th>Count</th><th>Denied $</th><th>Status</th></tr>
{carc_rows}</table></section>
<footer>Built by Codifyre AI &middot; github.com/iamjohnyogesh-bit/codifyre-ai-denial-management-analytics</footer>
</div></body></html>"""


def main():
    parser = argparse.ArgumentParser(description="Render a denial summary JSON as an HTML dashboard")
    parser.add_argument("json_path", help="Summary JSON from denial_analytics.py --json")
    parser.add_argument("-o", "--out", default="dashboard.html")
    args = parser.parse_args()

    with open(args.json_path, encoding="utf-8") as fh:
        summary = json.load(fh)
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(render(summary))
    print(f"dashboard written to {args.out}")


if __name__ == "__main__":
    main()
