# Codifyre AI - Denial Management Analytics

> Built by **Codifyre AI** - practical tools for healthcare revenue cycle work.

A small, dependency-free Python toolkit for healthcare revenue cycle teams to
analyze claim denials: KPIs by payer, reason code (CARC) and category, monthly
trends, appeal win rates, recovered dollars, and one-click draft appeal
letters for un-worked denials.

Built for billers, denial specialists, and RCM managers who get a denial
worklist as a CSV and need answers in seconds, not a spreadsheet afternoon.

## Features

- **Denial KPIs** - counts, billed dollars at risk, denial rate (when you pass total submitted claims)
- **Breakdowns** - top payers, denial categories, and CARC reason codes by denied dollars
- **Monthly trend** - denial volume and dollars over time
- **Appeal tracking** - filed / won / lost / pending, win rate, recovered amount
- **Appeal letter drafts** - category-specific letter templates (prior auth, timely filing, medical necessity, coding/modifier, eligibility, missing info) generated for every un-appealed, appealable denial
- **CARC/RARC reference** - common Claim Adjustment Reason Codes and Remittance Advice Remark Codes baked in
- **HTML dashboard** - render the JSON summary as a polished, self-contained dark-theme dashboard (KPI cards, payer/category/trend charts, CARC table) - opens in any browser, no internet needed
- **Zero dependencies** - Python 3.9+ standard library only

## Quickstart

```bash
# 1. Generate the sample worklist (90 realistic denials, reproducible)
python gen_sample_data.py

# 2. Run the analytics
python denial_analytics.py data/sample_denials.csv --total-claims 1000

# 3. Export JSON + draft appeal letters
python denial_analytics.py data/sample_denials.csv \
    --total-claims 1000 --json report.json --appeals appeals_out/

# 4. Render the HTML dashboard (see dashboard-sample.html for a sample)
python dashboard.py report.json -o dashboard.html
```

## Sample output

```
================================================================
RCM DENIAL ANALYTICS - MANAGEMENT SUMMARY
================================================================
Open/analyzed denials : 90
Billed $ at risk      : $104,125.79
Denial rate           : 9.0% of submitted claims

-- Top payers by denied dollars ------------------------------
  Aetna                          15 denials   $   18,371.56
  Medicare                       14 denials   $   17,600.89
  ...

-- Appeals -----------------------------------------------------
  Filed: 55   Won: 36   Lost: 10   Pending: 9
  Win rate: 78.3%   Recovered: $38,868.72
```

## Input CSV format

One row per denial. Required columns: `denial_id`, `claim_id`, `payer`,
`billed_amount`, `carc_code`. The rest are optional but used when present:

| column | notes |
| --- | --- |
| `date_of_service`, `denial_date` | `YYYY-MM-DD` (trend uses `denial_date`) |
| `cpt_code`, `icd10_code` | shown in appeal letters |
| `carc_code`, `rarc_code` | CARC drives category + appealability if `category` is blank |
| `category` | optional override |
| `appeal_filed` | `yes`/`no` |
| `appeal_outcome` | `won` / `lost` / `pending` (blank = not appealed) |
| `resolved_amount` | dollars recovered on a won appeal |

## Project structure

```
denial_analytics.py    CLI: load CSV, compute KPIs, print report, export JSON/appeals
denial_codes.py        CARC/RARC reference data + lookups
appeal_templates.py    Category-specific appeal letter templates
gen_sample_data.py     Deterministic sample worklist generator
dashboard.py           HTML dashboard renderer (self-contained, dark theme)
data/                  Sample CSV (generated)
tests/                 Unit tests (stdlib unittest)
```

## Run the tests

```bash
python -m unittest discover -s tests -v
```

## Roadmap

- 835 ERA file import (map remittances straight into the worklist)
- Payer-specific appeal address book

## License

MIT - see [LICENSE](LICENSE).

---

**Codifyre AI** - building useful tools, one project at a time.
