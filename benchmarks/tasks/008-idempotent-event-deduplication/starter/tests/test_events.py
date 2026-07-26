from copy import deepcopy
import math
import unittest

from events import deduplicate_events


class EventTests(unittest.TestCase):
    def test_keeps_earliest_retry_and_sorts_output(self):
        events = [
            {"id": "build", "timestamp": 30, "payload": {"ok": True}},
            {"id": "test", "timestamp": 20, "payload": ["unit"]},
            {"id": "build", "timestamp": 10, "payload": {"ok": True}},
        ]

        self.assertEqual(
            deduplicate_events(events),
            [
                {"id": "build", "timestamp": 10, "payload": {"ok": True}},
                {"id": "test", "timestamp": 20, "payload": ["unit"]},
            ],
        )

    def test_equal_timestamps_are_ordered_by_id(self):
        events = [
            {"id": "zeta", "timestamp": 1, "payload": None},
            {"id": "alpha", "timestamp": 1, "payload": None},
        ]

        self.assertEqual(
            [event["id"] for event in deduplicate_events(events)],
            ["alpha", "zeta"],
        )

    def test_reports_smallest_conflicting_id(self):
        events = [
            {"id": "zeta", "timestamp": 1, "payload": 1},
            {"id": "alpha", "timestamp": 1, "payload": 1},
            {"id": "zeta", "timestamp": 2, "payload": 2},
            {"id": "alpha", "timestamp": 2, "payload": 2},
        ]

        with self.assertRaisesRegex(ValueError, r"^conflicting event: alpha$"):
            deduplicate_events(events)

    def test_rejects_invalid_event_shapes(self):
        invalid = (
            None,
            [{"id": "a", "timestamp": 1}],
            [{"id": "a", "timestamp": 1, "payload": None, "extra": 1}],
            [{"id": "", "timestamp": 1, "payload": None}],
            [{"id": "a", "timestamp": True, "payload": None}],
            [{"id": "a", "timestamp": -1, "payload": None}],
        )
        for value in invalid:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    deduplicate_events(value)

    def test_rejects_non_json_payloads(self):
        invalid_payloads = (
            {1: "bad key"},
            {"value": math.inf},
            {"value": object()},
            (1, 2),
        )
        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    deduplicate_events(
                        [{"id": "a", "timestamp": 1, "payload": payload}]
                    )

    def test_result_does_not_share_payloads_with_input(self):
        events = [
            {"id": "a", "timestamp": 1, "payload": {"items": [1]}}
        ]
        before = deepcopy(events)

        result = deduplicate_events(events)
        result[0]["payload"]["items"].append(2)

        self.assertEqual(events, before)


if __name__ == "__main__":
    unittest.main()
