from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from benchmarks.attempts import (
    AttemptError,
    build_attempt_result,
    serialize_attempt_result,
)
from benchmarks.runner import BenchmarkError


class AttemptRunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repository_root = Path(__file__).resolve().parents[1]
        cls.task = (
            cls.repository_root
            / "benchmarks/tasks/001-safe-path-resolution"
        )
        cls.attempt = (
            cls.repository_root
            / "benchmark_runs/fixtures/001-reference-replay"
        )

    def _sandbox(self, directory: str) -> tuple[Path, Path]:
        root = Path(directory)
        task = root / "benchmarks/tasks/001-safe-path-resolution"
        attempt = root / "benchmark_runs/fixtures/001-reference-replay"
        shutil.copytree(self.task, task)
        shutil.copytree(self.attempt, attempt)
        return root, attempt / "attempt.json"

    def test_fixture_passes_but_is_not_scoreboard_eligible(self) -> None:
        result = build_attempt_result(
            self.attempt / "attempt.json",
            self.repository_root,
        )

        self.assertTrue(result["summary"]["solved"])
        self.assertFalse(result["summary"]["scoreboard_eligible"])
        self.assertEqual(result["provenance"]["kind"], "fixture")
        self.assertTrue(result["provenance"]["reference_access"])

    def test_result_is_deterministic(self) -> None:
        first = serialize_attempt_result(
            build_attempt_result(
                self.attempt / "attempt.json",
                self.repository_root,
            )
        )
        second = serialize_attempt_result(
            build_attempt_result(
                self.attempt / "attempt.json",
                self.repository_root,
            )
        )
        self.assertEqual(first, second)

    def test_disallowed_candidate_path_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root, manifest = self._sandbox(directory)
            disallowed = manifest.parent / "candidate/tests/test_path_guard.py"
            disallowed.parent.mkdir(parents=True)
            disallowed.write_text("raise SystemExit(0)\n", encoding="utf-8")

            with self.assertRaisesRegex(
                BenchmarkError,
                "candidate contains disallowed path",
            ):
                build_attempt_result(manifest, root)

    def test_disclosed_agent_run_can_be_scoreboard_eligible(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root, manifest = self._sandbox(directory)
            data = json.loads(manifest.read_text(encoding="utf-8"))
            data["provenance"] = {
                "kind": "agent",
                "agent_name": "example-agent",
                "agent_version": "1.0",
                "model": "example-model",
                "reference_access": False,
            }
            data["execution"]["elapsed_ms"] = 1200
            manifest.write_text(
                json.dumps(data, indent=2) + "\n",
                encoding="utf-8",
            )

            result = build_attempt_result(manifest, root)

        self.assertTrue(result["summary"]["scoreboard_eligible"])

    def test_failed_agent_run_is_not_scoreboard_eligible(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root, manifest = self._sandbox(directory)
            data = json.loads(manifest.read_text(encoding="utf-8"))
            data["provenance"] = {
                "kind": "agent",
                "agent_name": "example-agent",
                "agent_version": "1.0",
                "model": "example-model",
                "reference_access": False,
            }
            data["execution"]["elapsed_ms"] = 1200
            manifest.write_text(
                json.dumps(data, indent=2) + "\n",
                encoding="utf-8",
            )
            starter = (
                root
                / "benchmarks/tasks/001-safe-path-resolution"
                / "starter/path_guard.py"
            )
            shutil.copyfile(
                starter,
                manifest.parent / "candidate/path_guard.py",
            )

            result = build_attempt_result(manifest, root)

        self.assertFalse(result["summary"]["solved"])
        self.assertFalse(result["summary"]["scoreboard_eligible"])

    def test_agent_identity_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root, manifest = self._sandbox(directory)
            data = json.loads(manifest.read_text(encoding="utf-8"))
            data["provenance"]["kind"] = "agent"
            data["provenance"]["reference_access"] = False
            manifest.write_text(
                json.dumps(data, indent=2) + "\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                AttemptError,
                "must disclose agent_name and model",
            ):
                build_attempt_result(manifest, root)

    def test_non_finite_cost_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root, manifest = self._sandbox(directory)
            data = json.loads(manifest.read_text(encoding="utf-8"))
            data["usage"]["cost_usd"] = float("nan")
            manifest.write_text(
                json.dumps(data, indent=2) + "\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                AttemptError,
                "cost_usd must be null or non-negative",
            ):
                build_attempt_result(manifest, root)

    def test_artifact_path_cannot_escape_attempt_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root, manifest = self._sandbox(directory)
            data = json.loads(manifest.read_text(encoding="utf-8"))
            data["artifacts"] = [
                {"name": "outside", "path": "../../outside.txt"}
            ]
            manifest.write_text(
                json.dumps(data, indent=2) + "\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                AttemptError,
                "artifact path is outside",
            ):
                build_attempt_result(manifest, root)


if __name__ == "__main__":
    unittest.main()
