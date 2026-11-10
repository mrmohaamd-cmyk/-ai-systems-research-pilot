"""Independent synthetic gate cases; no model calls or runner invocation."""
import copy
import math
import unittest

from pilot import core as pilot


class FeasibilityScreenTests(unittest.TestCase):
    def setUp(self):
        self.config = pilot.read_json(pilot.ROOT / "config/live.template.json")
        self.report = {
            "verification_only": False, "study_type": "feasibility",
            "run_status": "complete", "missing_stage_records": 0,
            "unpriced_attempts": 0, "physical_calls": 300,
            "conditions": {c: {"planned_tasks": 60, "latency_complete_workflows_n": 60}
                           for c in "ABC"},
            "contrasts": {c: {"difference": .05, "regressions": 6}
                          for c in ("B_minus_A", "B_minus_C")},
        }
        self.report["conditions"]["B"].update(
            correct=30, known_standalone_cost_estimate_usd=3,
            p95_complete_request_time_s_exploratory=30)

    def test_exact_thresholds_pass_only_for_further_study(self):
        result = pilot.feasibility_screen(self.report, self.config)
        self.assertEqual(result["status"], "PASS_FURTHER_STUDY")
        self.assertEqual(len(result["checks"]), 6)
        self.assertTrue(all(result["checks"].values()))

    def test_each_threshold_fails_independently(self):
        cases = [
            ("contrasts", "B_minus_A", "difference", math.nextafter(.05, 0), "gain_over_A"),
            ("contrasts", "B_minus_C", "difference", math.nextafter(.05, 0), "gain_over_C"),
            ("contrasts", "B_minus_A", "regressions", 7, "regressions_vs_A"),
            ("contrasts", "B_minus_C", "regressions", 7, "regressions_vs_C"),
            ("conditions", "B", "p95_complete_request_time_s_exploratory",
             math.nextafter(30, math.inf), "B_request_p95"),
            ("conditions", "B", "known_standalone_cost_estimate_usd",
             math.nextafter(3, math.inf), "B_cost_per_correct"),
            ("conditions", "B", "correct", 0, "B_cost_per_correct"),
        ]
        for section, condition, field, value, failed_check in cases:
            with self.subTest(field=field, condition=condition):
                report = copy.deepcopy(self.report)
                report[section][condition][field] = value
                result = pilot.feasibility_screen(report, self.config)
                self.assertEqual(result["status"], "FAIL_FEASIBILITY_SCREEN")
                self.assertEqual([k for k, passed in result["checks"].items() if not passed],
                                 [failed_check])

    def test_each_incomplete_or_unpriced_guard_is_inconclusive(self):
        cases = [("run_status", "stopped"), ("missing_stage_records", 1),
                 ("unpriced_attempts", 1), ("physical_calls", 299), ("physical_calls", 301)]
        for field, value in cases:
            with self.subTest(field=field, value=value):
                report = copy.deepcopy(self.report)
                report[field] = value
                self.assertEqual(pilot.feasibility_screen(report, self.config)["status"],
                                 "INCONCLUSIVE")
        for condition in "ABC":
            with self.subTest(incomplete_condition=condition):
                report = copy.deepcopy(self.report)
                report["conditions"][condition]["latency_complete_workflows_n"] = 59
                self.assertEqual(pilot.feasibility_screen(report, self.config)["status"],
                                 "INCONCLUSIVE")


if __name__ == "__main__":
    unittest.main()
