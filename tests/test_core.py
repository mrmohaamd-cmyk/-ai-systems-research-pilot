import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pilot import core as pilot
from pilot.prepare_data import dump_rows, prepare


class PilotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.tasks = self.root / "tasks.jsonl"
        self.key = self.root / "key.jsonl"
        dump_rows(self.tasks, [
            {"id": "fixture-1", "question": "A crate contains 4 red and 5 blue balls. How many balls?"},
            {"id": "fixture-2", "question": "Three packs contain four pens each. How many pens?"},
            {"id": "fixture-3", "question": "A shop had 27 cups and sold 7. How many remain?"},
            {"id": "fixture-4", "question": "Share 16 apples equally among 4 people. How many per person?"}])
        dump_rows(self.key, [{"id": f"fixture-{i}", "answer": str(a)} for i, a in enumerate([9, 12, 20, 4], 1)])
        self.manifest = self.root / "manifest.json"
        pilot.write_json(self.manifest, {"purpose": "fixture-verification", "task_population": "four scripted test cases",
                                        "source_revision": "authored-fixtures-v1", "tasks_sha256": pilot.digest(self.tasks.read_bytes()),
                                        "key_sha256": pilot.digest(self.key.read_bytes())})
        self.config = self.root / "config.json"
        pilot.write_json(self.config, pilot.read_json(pilot.ROOT / "config/fixture.json"))
        self.frozen = self.root / "freeze.json"
        self.out = self.root / "run"
        pilot.freeze(self.config, self.tasks, self.manifest, self.frozen)

    def tearDown(self):
        self.temp.cleanup()

    def test_scorer_numeric_equivalence_and_rejection(self):
        self.assertEqual(pilot.answer("Calculation\nFINAL: 1,200.00"), pilot.numeric("1200"))
        self.assertEqual(pilot.answer("FINAL: -2.5"), pilot.numeric("-2.50"))
        for bad in ("FINAL: 1,2", "FINAL: NaN", "FINAL: 2 or 3", "2", "FINAL: 2\nFINAL: 3", "FINAL: 2\nextra", "FINAL: 2/3", "FINAL: 5%"):
            self.assertIsNone(pilot.answer(bad), bad)

    def test_task_keys_and_duplicate_questions_rejected(self):
        dump_rows(self.tasks, [{"id": "x", "question": "Q", "answer": "999secret"}])
        with self.assertRaises(ValueError):
            pilot.load_tasks(self.tasks)
        dump_rows(self.tasks, [{"id": "x", "question": "Q"}, {"id": "y", "question": "Q"}])
        with self.assertRaises(ValueError):
            pilot.load_tasks(self.tasks)

    def test_correct_pairing_and_fixed_denominator(self):
        pilot.run(self.frozen, self.tasks, self.out)
        report = pilot.analyze(self.out, self.key)
        self.assertEqual(report["physical_calls"], 20)
        self.assertEqual(report["conditions"]["A"]["correct"], 2)
        self.assertEqual(report["conditions"]["B"]["correct"], 2)
        self.assertEqual(report["conditions"]["C"]["correct"], 2)
        self.assertEqual(report["contrasts"]["B_minus_A"]["gains"], 1)
        self.assertEqual(report["contrasts"]["B_minus_A"]["regressions"], 1)
        self.assertTrue(report["verification_only"])
        self.assertEqual(report["decision"], "NO_EFFICACY_INFERENCE_FIXTURE")

    def test_shared_initial_and_no_answer_key_in_requests(self):
        pilot.run(self.frozen, self.tasks, self.out)
        events = pilot.rows(self.out / "events.jsonl")
        starts = {x["call_id"]: x for x in events if x["event"] == "start"}
        for i in range(1, 5):
            payloads = [json.loads(starts[f"fixture-{i}/{s}"]["messages"][1]["content"].split("INPUT DATA:\n")[1]) for s in ("B1", "C1")]
            self.assertEqual(payloads[0], payloads[1])
            self.assertEqual(set(payloads[0]), {"question", "initial_answer"})
        # Model adapter has no key path or labels in its arguments/config.
        self.assertNotIn(str(self.key), (self.out / "events.jsonl").read_text())

    def test_resume_sends_no_duplicate_requests(self):
        pilot.run(self.frozen, self.tasks, self.out)
        before = (self.out / "events.jsonl").read_bytes()
        def never(*args):
            raise AssertionError("Duplicate request")
        pilot.run(self.frozen, self.tasks, self.out, backend_override=never)
        self.assertEqual(before, (self.out / "events.jsonl").read_bytes())

    def test_interrupted_attempt_not_retried(self):
        def crash(*args):
            raise KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt):
            pilot.run(self.frozen, self.tasks, self.out, backend_override=crash)
        pilot.run(self.frozen, self.tasks, self.out)
        report = pilot.analyze(self.out, self.key)
        self.assertEqual(report["call_status_counts"]["interrupted_unknown"], 1)
        self.assertEqual(report["call_status_counts"]["skipped_dependency"], 4)
        self.assertEqual(report["conditions"]["A"]["planned_tasks"], 4)

    def test_timeout_and_missing_tasks_remain_in_denominator(self):
        def timeout(*args):
            raise TimeoutError()
        pilot.run(self.frozen, self.tasks, self.out, backend_override=timeout)
        report = pilot.analyze(self.out, self.key)
        self.assertEqual(report["physical_calls"], 4)
        self.assertEqual(report["call_status_counts"]["timeout_unknown_charge"], 4)
        self.assertEqual(report["unpriced_attempts"], 4)
        self.assertTrue(all(report["conditions"][c]["accuracy"] == 0 for c in "ABC"))

    def test_missing_usage_stops_and_blocks_resume(self):
        def no_usage(*args):
            return {"text": "FINAL: 9", "finish_reason": "stop"}
        result = pilot.run(self.frozen, self.tasks, self.out, backend_override=no_usage)
        self.assertEqual(result["status"], "stopped")
        report = pilot.analyze(self.out, self.key)
        self.assertEqual(report["missing_stage_records"], 19)
        again = pilot.run(self.frozen, self.tasks, self.out)
        self.assertEqual(again["physical_calls"], 1)

    def test_freeze_and_key_tamper_rejected(self):
        frozen = pilot.read_json(self.frozen)
        frozen["config"]["temperature"] = .9
        pilot.write_json(self.frozen, frozen)
        with self.assertRaises(ValueError):
            pilot.run(self.frozen, self.tasks, self.out)

    def test_key_hash_mismatch_rejected(self):
        pilot.run(self.frozen, self.tasks, self.out)
        self.key.write_text(self.key.read_text().replace('"9"', '"10"'))
        with self.assertRaises(ValueError):
            pilot.analyze(self.out, self.key)

    def test_no_adoption_from_no_discordance(self):
        result = pilot.paired_summary([1]*60, [1]*60)
        self.assertLess(result["familywise_95_interval"][0], 0)
        self.assertGreater(result["familywise_95_interval"][1], 0)
        self.assertEqual(result["mcnemar_exact_p_unadjusted"], 1)

    def test_binomial_interval_known_boundary(self):
        self.assertAlmostEqual(pilot.binomial_interval(0, 60)[1], 1 - .025**(1/60), places=10)
        self.assertAlmostEqual(pilot.binomial_interval(60, 60)[0], .025**(1/60), places=10)
        self.assertAlmostEqual(pilot.paired_summary([1]*6, [0]*6)["mcnemar_exact_p_unadjusted"], .03125)

    def test_live_template_fails_closed(self):
        with self.assertRaises(ValueError):
            pilot.validate_config(pilot.read_json(pilot.ROOT / "config/live.template.json"), pilot.read_json(self.manifest), 4)

    def test_budget_requires_entire_planned_sample(self):
        c = pilot.read_json(pilot.ROOT / "config/live.template.json")
        c.update(model="candidate", deployment_revision="test-revision", authority_reference="test-only", operator="test",
                 endpoint="https://example.test/chat/completions", task_population_accepted="fixture", execution_authorized=True,
                 budget_usd=1, per_call_reservation_usd=.1, input_usd_per_million=1, output_usd_per_million=2,
                 reservation_basis="test", price_source="test")
        with self.assertRaises(ValueError):
            pilot.validate_config(c, pilot.read_json(self.manifest), 4)
        c["budget_usd"] = 2
        pilot.validate_config(c, pilot.read_json(self.manifest), 4)

    def test_http_contract_without_network(self):
        c = pilot.read_json(pilot.ROOT / "config/live.template.json")
        c.update(endpoint="https://example.test/chat/completions", model="test-model")
        class Response:
            def __enter__(self): return self
            def __exit__(self, *a): pass
            def read(self, *a):
                return json.dumps({"id": "request-1", "model": "test-model", "choices": [{"finish_reason": "stop", "message": {"content": "FINAL: 9"}}],
                                   "usage": {"prompt_tokens": 32, "completion_tokens": 5}}).encode()
        with patch.dict("os.environ", {"PILOT_API_KEY": "test-secret"}), patch("urllib.request.build_opener") as opener:
            opener.return_value.open.return_value = Response()
            r = pilot.http_reply({"id": "x"}, "A", [{"role": "user", "content": "question"}], c)
            request = opener.return_value.open.call_args.args[0]
            payload = json.loads(request.data)
            self.assertEqual(payload["max_tokens"], 512)
            self.assertNotIn("tools", payload)
            self.assertNotIn("test-secret", request.data.decode())
            self.assertEqual(r["input_tokens"], 32)
            self.assertEqual(r["text"], "FINAL: 9")

    def test_request_size_limit_sends_nothing_and_keeps_denominator(self):
        c = pilot.read_json(self.config)
        c["max_request_bytes"] = 1
        pilot.write_json(self.config, c)
        frozen = self.root / "limited.json"
        pilot.freeze(self.config, self.tasks, self.manifest, frozen)
        result = pilot.run(frozen, self.tasks, self.out)
        report = pilot.analyze(self.out, self.key)
        self.assertEqual(result["physical_calls"], 0)
        self.assertEqual(report["call_status_counts"]["skipped_input_limit"], 4)
        self.assertEqual(report["missing_stage_records"], 0)
        self.assertEqual(report["conditions"]["A"]["planned_tasks"], 4)

    def test_cost_bound_incident_stops_live_adapter_and_resume(self):
        c = pilot.read_json(pilot.ROOT / "config/live.template.json")
        c.update(model="test-only", deployment_revision="test", authority_reference="unit test without network", operator="test",
                 endpoint="https://example.test/chat/completions", task_population_accepted="fixture", execution_authorized=True,
                 budget_usd=2, per_call_reservation_usd=.1, input_usd_per_million=1000, output_usd_per_million=1000,
                 reservation_basis="intentionally undersized test bound", price_source="test")
        pilot.write_json(self.config, c)
        frozen = self.root / "budget.json"
        pilot.freeze(self.config, self.tasks, self.manifest, frozen)
        with patch.dict("os.environ", {"PILOT_API_KEY": "test-only"}):
            first = pilot.run(frozen, self.tasks, self.out, backend_override=pilot.fixture_reply)
            second = pilot.run(frozen, self.tasks, self.out, backend_override=pilot.fixture_reply)
        self.assertEqual(first["physical_calls"], 1)
        self.assertEqual(second["physical_calls"], 1)
        report = pilot.analyze(self.out, self.key)
        self.assertEqual(report["call_status_counts"]["cost_bound_exceeded"], 1)
        self.assertAlmostEqual(report["known_physical_cost_estimate_usd"], .112)
        self.assertTrue(report["verification_only"])

    def test_exceeded_output_cap_stops_followup_calls(self):
        def too_many_tokens(task, stage, request, config):
            r = pilot.fixture_reply(task, stage, request, config)
            r["output_tokens"] = config["max_tokens"][stage] + 1
            return r
        result = pilot.run(self.frozen, self.tasks, self.out, backend_override=too_many_tokens)
        self.assertEqual(result["status"], "stopped")
        report = pilot.analyze(self.out, self.key)
        self.assertEqual(report["physical_calls"], 1)
        self.assertEqual(report["call_status_counts"]["usage_invalid"], 1)

    def test_unexpected_or_duplicate_ledger_records_rejected(self):
        start = {"event": "start", "call_id": "x/A"}
        with self.assertRaises(ValueError):
            pilot.audit_events([start, start], {"x/A"})
        with self.assertRaises(ValueError):
            pilot.audit_events([start], {"y/A"})

    def test_prepare_disjoint_split_and_provenance(self):
        source = self.root / "source"
        dump_rows(source / "train.jsonl", [{"question": "One plus two?", "answer": "#### 3"}])
        dump_rows(source / "test.jsonl", [{"question": "One plus two?", "answer": "#### 3"}, {"question": "Four plus five?", "answer": "#### 9"}])
        dest = self.root / "prepared"
        prepare(source, "a"*40, dest, dev_n=1, eval_n=1)
        self.assertEqual(pilot.read_json(dest / "eval_manifest.json")["cross_split_exact_duplicates_excluded"], 1)
        self.assertEqual(set(pilot.rows(dest / "eval_tasks.jsonl")[0]), {"id", "question"})


if __name__ == "__main__":
    unittest.main()
