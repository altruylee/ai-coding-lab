from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from benchmarks.campaigns import (
    CampaignError,
    _parse_campaign,
    build_campaign_result,
    serialize_campaign_result,
)


class CampaignRunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repository_root = Path(__file__).resolve().parents[1]
        cls.campaign = (
            cls.repository_root
            / "benchmark_runs/campaigns/task002-prompt-context-001"
            / "campaign.json"
        )

    def test_recorded_campaign_replays_all_attempts(self) -> None:
        result = build_campaign_result(
            self.campaign,
            self.repository_root,
        )

        self.assertEqual(result["summary"]["attempts"], 4)
        self.assertEqual(result["summary"]["solved"], 4)
        self.assertEqual(result["summary"]["scoreboard_eligible"], 4)
        self.assertEqual(result["summary"]["human_interventions"], 0)
        attempt_counts = [
            configuration["summary"]["attempts"]
            for configuration in result["configurations"]
        ]
        self.assertEqual(attempt_counts, [2, 2])

    def test_result_is_deterministic(self) -> None:
        first = serialize_campaign_result(
            build_campaign_result(self.campaign, self.repository_root)
        )
        second = serialize_campaign_result(
            build_campaign_result(self.campaign, self.repository_root)
        )

        self.assertEqual(first, second)

    def test_configuration_without_attempt_is_rejected(self) -> None:
        campaign = {
            "schema_version": 1,
            "campaign_id": "example",
            "task": "benchmarks/tasks/example",
            "configurations": [
                {"id": "used", "description": "used configuration"},
                {"id": "unused", "description": "unused configuration"},
            ],
            "attempts": [
                {
                    "configuration": "used",
                    "attempt": "benchmark_runs/example/attempt.json",
                }
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "campaign.json")
            path.write_text(
                json.dumps(campaign, indent=2) + "\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                CampaignError,
                "configuration\\(s\\) without attempts: unused",
            ):
                _parse_campaign(path)


if __name__ == "__main__":
    unittest.main()
