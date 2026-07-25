from __future__ import annotations

from pathlib import Path
import unittest

from benchmarks.runner import run_benchmark, serialize_result


class Task002Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        cls.task = (
            repository_root
            / "benchmarks/tasks/002-nested-secret-redaction"
        )

    def test_starter_fails_and_reference_passes(self) -> None:
        result = run_benchmark(self.task)

        self.assertTrue(result["summary"]["benchmark_valid"])
        self.assertEqual(result["starter"]["observed"], "fail")
        self.assertEqual(result["reference"]["observed"], "pass")
        self.assertNotEqual(result["starter"]["checks"][0]["exit_code"], 0)
        self.assertEqual(result["reference"]["checks"][0]["exit_code"], 0)

    def test_result_is_deterministic(self) -> None:
        first = serialize_result(run_benchmark(self.task))
        second = serialize_result(run_benchmark(self.task))

        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
