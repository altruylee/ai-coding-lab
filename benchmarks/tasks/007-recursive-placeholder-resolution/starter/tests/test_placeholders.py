from copy import deepcopy
import unittest

from placeholders import resolve_placeholders


class PlaceholderTests(unittest.TestCase):
    def test_resolves_nested_containers_and_preserves_types(self):
        value = {
            "command": ["run", "${TARGET}"],
            "metadata": ({"owner": "${OWNER}"}, "${TARGET}:${OWNER}"),
        }
        env = {"TARGET": "tests", "OWNER": "agent"}

        self.assertEqual(
            resolve_placeholders(value, env),
            {
                "command": ["run", "tests"],
                "metadata": ({"owner": "agent"}, "tests:agent"),
            },
        )

    def test_escape_produces_a_literal_placeholder(self):
        self.assertEqual(
            resolve_placeholders(
                "literal=$${TOKEN}; value=${TOKEN}",
                {"TOKEN": "redacted"},
            ),
            "literal=${TOKEN}; value=redacted",
        )

    def test_missing_variables_are_sorted_and_deduplicated(self):
        with self.assertRaisesRegex(
            ValueError,
            r"^missing variables: ALPHA, ZETA$",
        ):
            resolve_placeholders(
                ["${ZETA}", "${ALPHA}", "${ZETA}"],
                {},
            )

    def test_malformed_placeholders_are_rejected(self):
        malformed = ("${UNCLOSED", "${lower}", "${A-B}", "${}")
        for value in malformed:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    resolve_placeholders(value, {})

    def test_invalid_environment_and_dictionary_keys_are_rejected(self):
        invalid = (
            ("${A}", None),
            ("${A}", {1: "value"}),
            ("${A}", {"A": 1}),
            ({1: "${A}"}, {"A": "value"}),
        )
        for value, env in invalid:
            with self.subTest(value=value, env=env):
                with self.assertRaises(ValueError):
                    resolve_placeholders(value, env)

    def test_inputs_are_not_mutated(self):
        value = {"items": ["${A}"]}
        env = {"A": "value"}
        value_before = deepcopy(value)
        env_before = deepcopy(env)

        resolve_placeholders(value, env)

        self.assertEqual(value, value_before)
        self.assertEqual(env, env_before)

    def test_non_container_scalars_are_preserved(self):
        self.assertEqual(resolve_placeholders(3, {}), 3)
        self.assertIs(resolve_placeholders(None, {}), None)


if __name__ == "__main__":
    unittest.main()
