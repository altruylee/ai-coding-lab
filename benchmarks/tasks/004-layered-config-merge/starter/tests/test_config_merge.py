from copy import deepcopy
import unittest

from config_merge import merge_config_layers


class ConfigMergeTests(unittest.TestCase):
    def test_merges_nested_values_and_replaces_sequences(self):
        layers = [
            {
                "agent": {
                    "model": "small",
                    "limits": {"tokens": 1000, "tools": 3},
                },
                "paths": ["src"],
            },
            {
                "agent": {
                    "model": "large",
                    "limits": {"tokens": 2000},
                },
                "paths": ["src", "tests"],
            },
        ]

        self.assertEqual(
            merge_config_layers(layers),
            {
                "agent": {
                    "limits": {"tokens": 2000, "tools": 3},
                    "model": "large",
                },
                "paths": ["src", "tests"],
            },
        )

    def test_none_deletes_keys_at_any_depth(self):
        layers = [
            {"agent": {"timeout": 30, "model": "small"}, "debug": True},
            {"agent": {"timeout": None}, "debug": None},
        ]

        self.assertEqual(
            merge_config_layers(layers),
            {"agent": {"model": "small"}},
        )

    def test_dictionary_can_replace_scalar(self):
        self.assertEqual(
            merge_config_layers([{"agent": "auto"}, {"agent": {"mode": "safe"}}]),
            {"agent": {"mode": "safe"}},
        )

    def test_result_keys_are_sorted_recursively(self):
        result = merge_config_layers(
            [{"z": 1, "a": {"z": 2, "a": 3}, "m": 4}]
        )

        self.assertEqual(list(result), ["a", "m", "z"])
        self.assertEqual(list(result["a"]), ["a", "z"])

    def test_inputs_and_retained_containers_are_not_mutated_or_shared(self):
        layers = [{"agent": {"tools": ["read", "test"]}}]
        before = deepcopy(layers)

        result = merge_config_layers(layers)
        result["agent"]["tools"].append("write")

        self.assertEqual(layers, before)

    def test_empty_layers_are_supported(self):
        self.assertEqual(merge_config_layers([]), {})
        self.assertEqual(merge_config_layers(()), {})

    def test_invalid_layers_and_keys_are_rejected(self):
        invalid = (
            {"agent": {}},
            [None],
            [{1: "bad"}],
            [{"agent": {"": "bad"}}],
        )
        for value in invalid:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    merge_config_layers(value)


if __name__ == "__main__":
    unittest.main()
