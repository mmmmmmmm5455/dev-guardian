import argparse
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import orchestrator


class Agent2ValidationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def write(self, name, data):
        path = self.root / name
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def test_results_arrays_remain_accepted_for_both_aliases(self):
        for alias in ("agent2_output", "execution_"):
            for results in ([], [{}], ["legacy", None, 7]):
                with self.subTest(alias=alias, results=results):
                    path = self.write(alias + ".json", {"results": results})
                    self.assertEqual(
                        orchestrator.validate_json_file(path),
                        (True, f"Valid Agent 2 output — {len(results)} results"),
                    )

    def test_wrong_results_containers_are_rejected(self):
        for alias in ("agent2_output", "execution_"):
            for results in ("abc", "", {}, {"one": 1}, None, True, 3, 1.5):
                with self.subTest(alias=alias, results=results):
                    path = self.write(alias + ".json", {"results": results})
                    valid, message = orchestrator.validate_json_file(path)
                    self.assertFalse(valid)
                    self.assertIn("'results' must be an array", message)

    def test_agent2_requires_an_object(self):
        for alias in ("agent2_output", "execution_"):
            for data in ([], ["results"], "results", None, 2, False):
                with self.subTest(alias=alias, data=data):
                    path = self.write(alias + ".json", data)
                    valid, message = orchestrator.validate_json_file(path)
                    self.assertFalse(valid)
                    self.assertIn("must be a JSON object", message)

    def test_missing_results_and_malformed_json_are_rejected(self):
        for alias in ("agent2_output", "execution_"):
            with self.subTest(alias=alias):
                path = self.write(alias + ".json", {})
                self.assertEqual(orchestrator.validate_json_file(path),
                                 (False, "Missing 'results' array"))
                path.write_text("{", encoding="utf-8")
                valid, message = orchestrator.validate_json_file(path)
                self.assertFalse(valid)
                self.assertTrue(message.startswith("Invalid JSON:"))

    def test_other_output_validation_is_preserved(self):
        controls = [
            ("agent1_output.json", {"discovery_id": "d", "scanned_paths": [],
                                    "total_found": 0, "skills": []}),
            ("discovery_control.json", {"discovery_id": "d", "scanned_paths": [],
                                       "total_found": 0, "skills": []}),
            ("agent3_output.json", {"repair_id": "r", "repairs_applied": [],
                                    "unfixable_issues": [], "total_fixed": 0,
                                    "total_unfixable": 0}),
            ("repair_control.json", {"repair_id": "r", "repairs_applied": [],
                                     "unfixable_issues": [], "total_fixed": 0,
                                     "total_unfixable": 0}),
        ]
        controls.extend(("generic.json", data) for data in
                        ([], None, "text", 2, {"results": "text"}))
        for name, data in controls:
            with self.subTest(name=name, data=data):
                self.assertTrue(orchestrator.validate_json_file(self.write(name, data))[0])

    def test_invalid_input_skips_cross_check(self):
        invalid = self.write("execution_invalid.json", {"results": "abc"})
        other = self.write("repair_control.json", {"repair_id": "r",
                           "repairs_applied": [], "unfixable_issues": [],
                           "total_fixed": 0, "total_unfixable": 0})
        output = io.StringIO()
        with patch.object(orchestrator, "validate_outputs_consistency") as cross_check:
            with contextlib.redirect_stdout(output), self.assertRaises(SystemExit) as exit:
                orchestrator.cmd_validate(argparse.Namespace(
                    files=[invalid, other], cross_check=True))
            self.assertEqual(exit.exception.code, 1)
            cross_check.assert_not_called()
        self.assertIn("[FAIL]", output.getvalue())

    def test_valid_input_still_runs_cross_check(self):
        valid = self.write("execution_valid.json", {"results": []})
        other = self.write("repair_control.json", {"repair_id": "r",
                           "repairs_applied": [], "unfixable_issues": [],
                           "total_fixed": 0, "total_unfixable": 0})
        with contextlib.redirect_stdout(io.StringIO()):
            with patch.object(orchestrator, "validate_outputs_consistency",
                              return_value=[]) as cross_check:
                orchestrator.cmd_validate(argparse.Namespace(
                    files=[valid, other], cross_check=True))
                cross_check.assert_called_once_with(valid, other)


if __name__ == "__main__":
    unittest.main()
