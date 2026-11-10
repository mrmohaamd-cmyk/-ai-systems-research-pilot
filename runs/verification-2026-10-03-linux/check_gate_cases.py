"""Record each boundary subtest while using the complete imported pilot runtime."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests'))
from test_feasibility import FeasibilityScreenTests

class Results(unittest.TextTestResult):
    cases = []
    def addSubTest(self, test, subtest, err):
        self.cases.append({'test': test.id(), 'case': str(subtest), 'passed': err is None})
        super().addSubTest(test, subtest, err)

runner = unittest.TextTestRunner(verbosity=2, resultclass=Results)
result = runner.run(unittest.defaultTestLoader.loadTestsFromTestCase(FeasibilityScreenTests))
record = {'tests_run': result.testsRun, 'successful': result.wasSuccessful(), 'subcases': result.cases}
print(json.dumps(record, indent=2))
if not result.wasSuccessful():
    raise SystemExit(1)
