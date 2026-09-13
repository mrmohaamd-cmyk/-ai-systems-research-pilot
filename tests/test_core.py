import json
import tempfile
import unittest
from pathlib import Path

from pilot.core import MockBackend, load_tasks, run, write_jsonl


class PilotTests(unittest.TestCase):
    def test_load_and_run_all_conditions(self):
        tasks = load_tasks("data/dev.jsonl")
        for condition in ("direct", "critique_revision", "additional_effort"):
            records = run(tasks, condition, MockBackend(), "test-run")
            self.assertEqual(len(records), 3)
            self.assertTrue(all(record["status"] == "ok" for record in records))
        revised = run(tasks[:1], "critique_revision", MockBackend(), "test-run")[0]
        self.assertEqual(revised["calls"], 3)
        self.assertIn("critique_text", revised)

    def test_write_jsonl(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nested" / "run.jsonl"
            write_jsonl(str(path), [{"ok": True}])
            self.assertEqual(json.loads(path.read_text())["ok"], True)


if __name__ == "__main__":
    unittest.main()
