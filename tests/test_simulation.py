"""Tests for the campaign simulation and the analysis."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd  # noqa: E402

from analyze import Data, behaviour, enrich, rates  # noqa: E402
from simulate_campaign import simulate  # noqa: E402

TABLES = simulate(600, 42)
EV = enrich(Data(TABLES["employees"], TABLES["campaigns"].assign(
    send_date=pd.to_datetime(TABLES["campaigns"]["send_date"])).assign(wave=[1, 2, 3]),
    TABLES["templates"], TABLES["events"]))


class Simulation(unittest.TestCase):
    def test_is_reproducible(self):
        again = simulate(600, 42)
        for name in TABLES:
            pd.testing.assert_frame_equal(TABLES[name], again[name])

    def test_one_row_per_campaign_and_employee(self):
        self.assertEqual(len(TABLES["events"]), 600 * 3)
        self.assertFalse(TABLES["events"].duplicated(["campaign_id", "employee_id"]).any())

    def test_funnel_is_consistent(self):
        self.assertTrue((EV["clicked"] <= EV["opened"]).all())
        self.assertTrue((EV["submitted"] <= EV["clicked"]).all())
        self.assertTrue((EV["opened"] <= EV["delivered"]).all())

    def test_timestamps_are_ordered(self):
        e = TABLES["events"]
        self.assertTrue((e["opened_at"].dropna() >= e.loc[e["opened_at"].notna(), "sent_at"]).all())
        c = e.dropna(subset=["clicked_at"])
        self.assertTrue((c["clicked_at"] >= c["opened_at"]).all())
        s = e.dropna(subset=["submitted_at"])
        self.assertTrue((s["submitted_at"] >= s["clicked_at"]).all())

    def test_rates_are_plausible(self):
        r = rates(EV.assign(all="all"), "all").iloc[0]
        self.assertTrue(0.05 < r["clicked_rate"] < 0.35)
        self.assertTrue(0.4 < r["opened_rate"] < 0.8)

    def test_training_effect_shows_up(self):
        by_wave = rates(EV, "wave").set_index("wave")
        self.assertLess(by_wave.loc[3, "clicked_rate"], by_wave.loc[1, "clicked_rate"])
        self.assertGreater(by_wave.loc[3, "reported_rate"], by_wave.loc[1, "reported_rate"])

    def test_security_team_clicks_less_than_commercial(self):
        d = rates(EV, "department").set_index("department")
        self.assertLess(d.loc["Segurança da Informação", "clicked_rate"],
                        d.loc["Comercial", "clicked_rate"])


class Analysis(unittest.TestCase):
    def test_rates_on_a_tiny_frame(self):
        df = pd.DataFrame({"employee_id": list("abcd"), "g": ["x"] * 4,
                           "delivered": [1, 1, 1, 0], "opened": [1, 1, 0, 0],
                           "clicked": [1, 0, 0, 0], "submitted": [0, 0, 0, 0],
                           "reported": [0, 1, 0, 0]})
        r = rates(df, "g").iloc[0]
        self.assertEqual(r["delivered"], 3)
        self.assertAlmostEqual(r["clicked_rate"], 1 / 3)
        self.assertAlmostEqual(r["reported_rate"], 1 / 3)
        self.assertAlmostEqual(r["report_to_click"], 1.0)

    def test_behaviour_counts_repeat_clickers(self):
        b = behaviour(EV)
        per = EV.groupby("employee_id")["clicked"].sum()
        self.assertEqual(b["repeat_clickers"], int((per >= 2).sum()))
        self.assertEqual(b["never_clicked"], int((per == 0).sum()))

    def test_outcomes_are_mutually_exclusive_and_complete(self):
        self.assertEqual(EV["outcome"].isna().sum(), 0)
        self.assertEqual(len(EV), 600 * 3)
        self.assertTrue(set(EV["outcome"]) <= {"submitted", "clicked", "reported", "opened",
                                               "ignored", "undelivered"})


if __name__ == "__main__":
    unittest.main()
