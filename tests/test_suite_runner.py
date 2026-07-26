from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from benchmarks.suites import (
    SuiteError,
    _load_suite,
    build_suite_result,
    serialize_suite_result,
)


class SuiteRunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repository_root = Path(__file__).resolve().parents[1]
        cls.suite = (
            cls.repository_root
            / "benchmark_runs/suites/first-multitask-prompt-context-001"
            / "suite.json"
        )

    def test_recorded_suite_replays_all_attempts(self) -> None:
        result = build_suite_result(self.suite, self.repository_root)

        self.assertEqual(result["summary"]["attempts"], 6)
        self.assertEqual(result["summary"]["solved"], 5)
        self.assertEqual(result["summary"]["scoreboard_eligible"], 5)
        self.assertEqual(result["summary"]["human_interventions"], 0)
        solved_by_configuration = {
            configuration["id"]: configuration["summary"]["solved"]
            for configuration in result["configurations"]
        }
        self.assertEqual(
            solved_by_configuration,
            {"spec-only": 2, "public-test-descriptions": 3},
        )

    def test_result_is_deterministic(self) -> None:
        first = serialize_suite_result(
            build_suite_result(self.suite, self.repository_root)
        )
        second = serialize_suite_result(
            build_suite_result(self.suite, self.repository_root)
        )

        self.assertEqual(first, second)

    def test_duplicate_campaign_path_is_rejected(self) -> None:
        suite = {
            "schema_version": 1,
            "suite_id": "example",
            "campaigns": [
                {"id": "first", "campaign": "same.json"},
                {"id": "second", "campaign": "same.json"},
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "suite.json")
            path.write_text(
                json.dumps(suite, indent=2) + "\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                SuiteError,
                "duplicate campaign path",
            ):
                _load_suite(path)


if __name__ == "__main__":
    unittest.main()
