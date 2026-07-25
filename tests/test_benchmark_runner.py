from __future__ import annotations

import hashlib
from pathlib import Path
import shutil
import tempfile
import unittest

from benchmarks.runner import _task_hash, run_benchmark, serialize_result


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

    def test_task_hash_uses_portable_relative_path_order(self) -> None:
        files = {
            "TASK.md": b"task",
            "reference/path_guard.py": b"reference",
            "starter/path_guard.py": b"starter",
        }
        with tempfile.TemporaryDirectory() as directory:
            task = Path(directory, "task")
            for relative, content in files.items():
                path = task / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)

            expected = hashlib.sha256()
            for relative in sorted(files):
                expected.update(relative.encode("utf-8"))
                expected.update(b"\0")
                expected.update(files[relative])
                expected.update(b"\0")

            self.assertEqual(_task_hash(task), expected.hexdigest())


if __name__ == "__main__":
    unittest.main()
