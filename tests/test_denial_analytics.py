import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gen_sample_data
from denial_analytics import load_denials, summarize, write_appeals
from denial_codes import describe_carc
from appeal_templates import generate_appeal
from dashboard import render


class DenialAnalyticsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.csv_path = os.path.join(cls.tmp, "sample.csv")
        rows = gen_sample_data.generate(90)
        import csv as csv_mod
        with open(cls.csv_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv_mod.DictWriter(fh, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        cls.denials = load_denials(cls.csv_path)

    def test_loads_all_rows(self):
        self.assertEqual(len(self.denials), 90)
        self.assertTrue(all(d.denial_id.startswith("DN2026") for d in self.denials))
        self.assertTrue(all(d.billed_amount > 0 for d in self.denials))

    def test_category_filled_from_carc(self):
        # sample rows leave category blank; loader derives it from CARC
        d = next(x for x in self.denials if x.carc_code == "197")
        self.assertEqual(d.category, "Prior authorization")

    def test_summary_math(self):
        s = summarize(self.denials, total_claims=1000)
        self.assertEqual(s["denial_count"], 90)
        self.assertAlmostEqual(
            s["total_billed_at_risk"],
            round(sum(d.billed_amount for d in self.denials), 2), places=2)
        self.assertEqual(s["denial_rate_pct"], 9.0)
        self.assertTrue(s["by_payer"])
        self.assertTrue(s["monthly_trend"])
        a = s["appeals"]
        self.assertEqual(a["won"] + a["lost"] + a["pending"], a["filed"])

    def test_reason_codes_have_descriptions(self):
        s = summarize(self.denials)
        for row in s["by_reason_code"]:
            self.assertNotEqual(row["description"], "Unknown adjustment reason")

    def test_carc_lookup(self):
        desc, cat, appealable = describe_carc("29")
        self.assertIn("filing", desc.lower())
        self.assertEqual(cat, "Timely filing")
        self.assertTrue(appealable)
        desc, cat, appealable = describe_carc("45")
        self.assertFalse(appealable)

    def test_appeal_letter_content(self):
        d = self.denials[0]
        letter = generate_appeal(d, provider_name="Test Clinic")
        self.assertIn(d.claim_id, letter)
        self.assertIn(d.payer, letter)
        self.assertIn("Test Clinic", letter)
        self.assertIn(f"${d.billed_amount:,.2f}", letter)

    def test_write_appeals_skips_filed_and_non_appealable(self):
        out_dir = os.path.join(self.tmp, "appeals")
        n = write_appeals(self.denials, out_dir, "Test Clinic")
        expected = sum(
            1 for d in self.denials
            if not d.appeal_filed and describe_carc(d.carc_code)[2])
        self.assertEqual(n, expected)
        self.assertEqual(len(os.listdir(out_dir)), n)

    def test_dashboard_render(self):
        s = summarize(self.denials, total_claims=1000)
        page = render(s)
        self.assertIn("Codifyre AI", page)
        self.assertIn("Monthly trend", page)
        self.assertIn("CARC", page)
        self.assertIn("$", page)
        # dark/light theme switch
        self.assertIn('id="theme-toggle"', page)
        self.assertIn("body.light", page)
        self.assertIn("localStorage", page)

    def test_empty_worklist(self):
        s = summarize([])
        self.assertEqual(s["denial_count"], 0)


if __name__ == "__main__":
    unittest.main()
