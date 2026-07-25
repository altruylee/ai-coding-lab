from __future__ import annotations

from copy import deepcopy
import unittest

from planner import resolve_task_order


class PlannerTests(unittest.TestCase):
    def test_resolves_a_linear_pipeline(self) -> None:
        tasks = {
            "build": [],
            "test": ["build"],
            "package": ["test"],
            "deploy": ["package"],
        }

        self.assertEqual(
            resolve_task_order(tasks),
            ["build", "test", "package", "deploy"],
        )

    def test_uses_lexicographic_order_for_ready_tasks(self) -> None:
        tasks = {
            "deploy": ["package", "docs"],
            "package": ["test"],
            "docs": ["lint"],
            "test": ["build"],
            "lint": ["build"],
            "build": [],
        }

        self.assertEqual(
            resolve_task_order(tasks),
            ["build", "lint", "docs", "test", "package", "deploy"],
        )

    def test_result_is_independent_of_dictionary_insertion_order(self) -> None:
        forward = {
            "alpha": [],
            "beta": [],
            "release": ["beta", "alpha"],
        }
        reverse = {
            "release": ["beta", "alpha"],
            "beta": [],
            "alpha": [],
        }

        self.assertEqual(
            resolve_task_order(forward),
            ["alpha", "beta", "release"],
        )
        self.assertEqual(
            resolve_task_order(reverse),
            ["alpha", "beta", "release"],
        )

    def test_duplicate_dependencies_do_not_duplicate_tasks(self) -> None:
        tasks = {
            "build": [],
            "test": ["build", "build"],
        }

        self.assertEqual(resolve_task_order(tasks), ["build", "test"])

    def test_unknown_dependency_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "unknown dependency: deploy -> package",
        ):
            resolve_task_order({"deploy": ["package"]})

    def test_cycles_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "dependency cycle"):
            resolve_task_order({"alpha": ["beta"], "beta": ["alpha"]})

        with self.assertRaisesRegex(ValueError, "dependency cycle"):
            resolve_task_order({"alpha": ["alpha"]})

    def test_invalid_names_and_collections_are_rejected(self) -> None:
        invalid_values = (
            {"": []},
            {1: []},
            {"build": "prepare"},
            {"build": [1]},
        )
        for value in invalid_values:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    resolve_task_order(value)

    def test_does_not_mutate_input_and_handles_empty_input(self) -> None:
        tasks = {
            "build": [],
            "test": ["build", "build"],
        }
        before = deepcopy(tasks)

        resolve_task_order(tasks)

        self.assertEqual(tasks, before)
        self.assertEqual(resolve_task_order({}), [])


if __name__ == "__main__":
    unittest.main()
