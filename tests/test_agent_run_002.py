from __future__ import annotations

from pathlib import Path
import unittest

from benchmarks.attempts import build_attempt_result


class AgentRun002Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repository_root = Path(__file__).resolve().parents[1]
        cls.attempt = (
            cls.repository_root
            / "benchmark_runs/agents/002-codex-blind-001/attempt.json"
        )

    def test_recorded_candidate_passes_and_is_eligible(self) -> None:
        result = build_attempt_result(self.attempt, self.repository_root)

        self.assertTrue(result["summary"]["solved"])
        self.assertTrue(result["summary"]["scoreboard_eligible"])
        self.assertFalse(result["summary"]["usage_complete"])
        self.assertEqual(result["candidate"]["changed_paths"], ["redactor.py"])
        self.assertEqual(result["execution"]["human_interventions"], 0)
        self.assertFalse(result["provenance"]["reference_access"])
        self.assertEqual(
            [artifact["name"] for artifact in result["artifacts"]],
            ["prompt", "attestation"],
        )


if __name__ == "__main__":
    unittest.main()
