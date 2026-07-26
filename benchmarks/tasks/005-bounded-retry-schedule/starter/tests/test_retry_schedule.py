import math
import unittest

from retry_schedule import build_retry_delays


class RetryScheduleTests(unittest.TestCase):
    def test_builds_exponential_schedule(self):
        self.assertEqual(
            build_retry_delays(5, 1, 10, [0, 0, 0, 0]),
            [1.0, 2.0, 4.0, 8.0],
        )

    def test_caps_before_and_after_jitter(self):
        self.assertEqual(
            build_retry_delays(6, 2, 10, [0, 0, 0.5, 0.5, -0.5]),
            [2.0, 4.0, 10.0, 10.0, 5.0],
        )

    def test_rounds_to_six_places(self):
        self.assertEqual(
            build_retry_delays(2, 0.1, 1, [1 / 3]),
            [0.133333],
        )

    def test_one_attempt_has_no_delays(self):
        self.assertEqual(build_retry_delays(1, 1, 2, []), [])

    def test_jitter_is_not_mutated(self):
        jitter = [0.1, -0.1]
        before = list(jitter)

        build_retry_delays(3, 1, 5, jitter)

        self.assertEqual(jitter, before)

    def test_invalid_scalar_inputs_are_rejected(self):
        invalid_calls = (
            (True, 1, 2, []),
            (0, 1, 2, []),
            (21, 1, 2, [0] * 20),
            (2, True, 2, [0]),
            (2, 0, 2, [0]),
            (2, math.inf, math.inf, [0]),
            (2, 2, 1, [0]),
        )
        for arguments in invalid_calls:
            with self.subTest(arguments=arguments):
                with self.assertRaises(ValueError):
                    build_retry_delays(*arguments)

    def test_invalid_jitter_is_rejected(self):
        invalid = (
            None,
            [],
            [0, 0],
            [True],
            [0.6],
            [math.nan],
        )
        for jitter in invalid:
            with self.subTest(jitter=jitter):
                with self.assertRaises(ValueError):
                    build_retry_delays(2, 1, 2, jitter)


if __name__ == "__main__":
    unittest.main()
