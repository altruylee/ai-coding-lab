from __future__ import annotations

from copy import deepcopy
import unittest

from redactor import redact_sensitive_values


class RedactorTests(unittest.TestCase):
    def test_redacts_exact_top_level_keys(self) -> None:
        value = {
            "password": "value-one",
            "secret": "value-two",
            "token": "value-three",
        }

        self.assertEqual(
            redact_sensitive_values(value),
            {
                "password": "[REDACTED]",
                "secret": "[REDACTED]",
                "token": "[REDACTED]",
            },
        )

    def test_redacts_nested_headers_and_arguments(self) -> None:
        value = {
            "request": {
                "headers": {
                    "Authorization": "value-one",
                    "Cookie": "value-two",
                }
            },
            "tool_calls": [
                {"arguments": {"api-key": "value-three"}},
            ],
        }

        self.assertEqual(
            redact_sensitive_values(value),
            {
                "request": {
                    "headers": {
                        "Authorization": "[REDACTED]",
                        "Cookie": "[REDACTED]",
                    }
                },
                "tool_calls": [
                    {"arguments": {"api-key": "[REDACTED]"}},
                ],
            },
        )

    def test_normalizes_case_and_preserves_tuples(self) -> None:
        value = (
            "event",
            {
                "ACCESS-TOKEN": "value-one",
                "API_KEY": "value-two",
                "PASSWORD": "value-three",
            },
        )

        self.assertEqual(
            redact_sensitive_values(value),
            (
                "event",
                {
                    "ACCESS-TOKEN": "[REDACTED]",
                    "API_KEY": "[REDACTED]",
                    "PASSWORD": "[REDACTED]",
                },
            ),
        )

    def test_does_not_redact_partial_key_matches(self) -> None:
        value = {
            "token_count": 3,
            "secretary": "example",
            "monkey": "example",
        }

        self.assertEqual(redact_sensitive_values(value), value)

    def test_recurses_under_non_string_keys_without_mutation(self) -> None:
        value = {
            1: {
                "password": "value-one",
                "items": [{"token": "value-two"}],
            }
        }
        before = deepcopy(value)

        result = redact_sensitive_values(value)

        self.assertEqual(
            result,
            {
                1: {
                    "password": "[REDACTED]",
                    "items": [{"token": "[REDACTED]"}],
                }
            },
        )
        self.assertEqual(value, before)
        self.assertIsNot(result, value)
        self.assertIsNot(result[1], value[1])

    def test_preserves_scalar_values(self) -> None:
        for value in (None, True, 7, 1.5, "plain text"):
            with self.subTest(value=value):
                self.assertEqual(redact_sensitive_values(value), value)


if __name__ == "__main__":
    unittest.main()
