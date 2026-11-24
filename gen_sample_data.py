#!/usr/bin/env python3
"""Generate a realistic sample denial worklist CSV for demo/testing.

Deterministic (seeded) so the repo's sample output is reproducible:
    python gen_sample_data.py            # writes data/sample_denials.csv
    python gen_sample_data.py --rows 200 --out data/big.csv
"""

import argparse
import csv
import os
import random

PAYERS = ["Aetna", "UnitedHealthcare", "Cigna", "BCBS", "Medicare", "Humana"]
CPTS = ["99213", "99214", "99215", "99203", "99204", "36415", "85025",
        "80053", "93000", "71046", "73721", "29881", "43239", "20610"]
ICD10S = ["M54.5", "E11.9", "I10", "J06.9", "R07.9", "K21.9", "M17.11",
          "N39.0", "R51.9", "Z00.00", "S83.511A", "E78.5"]
# (carc, rarc, weight) - weights mirror typical denial mix
REASONS = [
    ("16", "MA130", 18), ("4", "M51", 12), ("197", "N517", 14),
    ("50", "N386", 10), ("97", "M80", 9), ("18", "N522", 7),
    ("29", "N30", 5), ("27", "N30", 5), ("22", "N479", 5),
    ("45", "", 6), ("1", "", 5), ("96", "", 4),
]


def generate(rows, seed=42):
    rng = random.Random(seed)
    carcs, weights = zip(*[(r[:2], r[2]) for r in REASONS])
    out = []
    for i in range(1, rows + 1):
        month = rng.randint(1, 6)  # Jun..Nov 2026
        denial_day = rng.randint(1, 28)
        dos_day = max(1, denial_day - rng.randint(5, 25))
        dos_month = month if denial_day > 25 else max(1, month - 1)
        carc, rarc = rng.choices(carcs, weights=weights, k=1)[0]
        billed = round(rng.uniform(45, 2400), 2)
        appealed = rng.random() < 0.55
        outcome = ""
        resolved = 0.0
        if appealed:
            roll = rng.random()
            if roll < 0.55:
                outcome = "won"
                resolved = round(billed * rng.uniform(0.7, 1.0), 2)
            elif roll < 0.85:
                outcome = "lost"
            else:
                outcome = "pending"
        out.append({
            "denial_id": f"DN{2026}{i:05d}",
            "claim_id": f"CLM{rng.randint(100000, 999999)}",
            "date_of_service": f"2026-{dos_month + 5:02d}-{dos_day:02d}",
            "denial_date": f"2026-{month + 5:02d}-{denial_day:02d}",
            "payer": rng.choice(PAYERS),
            "cpt_code": rng.choice(CPTS),
            "icd10_code": rng.choice(ICD10S),
            "billed_amount": f"{billed:.2f}",
            "carc_code": carc,
            "rarc_code": rarc,
            "category": "",
            "appeal_filed": "yes" if appealed else "no",
            "appeal_outcome": outcome,
            "resolved_amount": f"{resolved:.2f}" if resolved else "",
        })
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=90)
    parser.add_argument("--out", default=os.path.join("data", "sample_denials.csv"))
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    rows = generate(args.rows, seed=args.seed)
    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} denials to {args.out}")


if __name__ == "__main__":
    main()
