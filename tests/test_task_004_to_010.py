from __future__ import annotations

from pathlib import Path
import unittest

from benchmarks.runner import run_benchmark, serialize_result


TASKS = (
    "004-layered-config-merge",
    "005-bounded-retry-schedule",
    "006-safe-archive-members",
    "007-recursive-placeholder-resolution",
    "008-idempotent-event-deduplication",
    "009-context-window-selection",
    "010-non-overlapping-text-edits",
)


class CompletedTaskSuiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        cls.tasks_root = repository_root / "benchmarks/tasks"

    def test_each_starter_fails_and_reference_passes(self) -> None:
        for task_name in TASKS:
            with self.subTest(task=task_name):
                result = run_benchmark(self.tasks_root / task_name)

                self.assertTrue(result["summary"]["benchmark_valid"])
                self.assertEqual(result["starter"]["observed"], "fail")
                self.assertEqual(result["reference"]["observed"], "pass")
                self.assertNotEqual(
                    result["starter"]["checks"][0]["exit_code"],
                    0,
                )
                self.assertEqual(
                    result["reference"]["checks"][0]["exit_code"],
                    0,
                )

    def test_each_result_is_deterministic(self) -> None:
        for task_name in TASKS:
            with self.subTest(task=task_name):
                task = self.tasks_root / task_name
                first = serialize_result(run_benchmark(task))
                second = serialize_result(run_benchmark(task))

                self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
