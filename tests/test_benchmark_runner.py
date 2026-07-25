from __future__ import annotations

from pathlib import Path
import shutil
import tempfile
import unittest

from benchmarks.runner import run_benchmark, serialize_result


class BenchmarkRunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repository_root = Path(__file__).resolve().parents[1]
        cls.task_dir = (
            cls.repository_root
            / "benchmarks/tasks/001-safe-path-resolution"
        )

    def test_starter_fails_and_reference_passes(self) -> None:
        result = run_benchmark(self.task_dir)

        self.assertTrue(result["summary"]["benchmark_valid"])
        self.assertEqual(result["starter"]["observed"], "fail")
        self.assertEqual(result["reference"]["observed"], "pass")
        self.assertEqual(result["starter"]["checks"][0]["exit_code"], 1)
        self.assertEqual(result["reference"]["checks"][0]["exit_code"], 0)

    def test_result_is_deterministic(self) -> None:
        first = serialize_result(run_benchmark(self.task_dir))
        second = serialize_result(run_benchmark(self.task_dir))
        self.assertEqual(first, second)

    def test_python_cache_does_not_change_task_result(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            copied_task = Path(directory, "task")
            shutil.copytree(self.task_dir, copied_task)
            before = serialize_result(run_benchmark(copied_task))
            cache = copied_task / "starter/__pycache__"
            cache.mkdir(exist_ok=True)
            (cache / "path_guard.cpython-312.pyc").write_bytes(b"cache noise")
            after = serialize_result(run_benchmark(copied_task))
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
