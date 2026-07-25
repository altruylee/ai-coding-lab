from copy import deepcopy
import unittest

from context_window import select_context_messages


def message(role, content, tokens):
    return {"role": role, "content": content, "tokens": tokens}


class ContextWindowTests(unittest.TestCase):
    def test_keeps_system_and_latest_user_then_fills_from_newest(self):
        messages = [
            message("system", "policy", 2),
            message("user", "old question", 4),
            message("assistant", "old answer", 4),
            message("tool", "small result", 1),
            message("user", "current question", 3),
            message("assistant", "draft", 2),
        ]

        self.assertEqual(
            select_context_messages(messages, 8),
            [
                message("system", "policy", 2),
                message("tool", "small result", 1),
                message("user", "current question", 3),
                message("assistant", "draft", 2),
            ],
        )

    def test_skips_large_recent_message_and_keeps_smaller_older_one(self):
        messages = [
            message("system", "policy", 1),
            message("assistant", "small", 1),
            message("assistant", "too large", 5),
            message("user", "current", 2),
        ]

        self.assertEqual(
            select_context_messages(messages, 4),
            [
                message("system", "policy", 1),
                message("assistant", "small", 1),
                message("user", "current", 2),
            ],
        )

    def test_all_system_messages_are_mandatory(self):
        messages = [
            message("system", "one", 1),
            message("assistant", "optional", 1),
            message("system", "two", 1),
        ]

        self.assertEqual(
            select_context_messages(messages, 2),
            [message("system", "one", 1), message("system", "two", 1)],
        )

    def test_mandatory_overflow_is_rejected(self):
        messages = [
            message("system", "policy", 3),
            message("user", "question", 2),
        ]
        with self.assertRaisesRegex(
            ValueError,
            r"^mandatory messages exceed budget$",
        ):
            select_context_messages(messages, 4)

    def test_invalid_inputs_are_rejected(self):
        invalid_calls = (
            (None, 1),
            ([], True),
            ([], -1),
            ([{"role": "user", "content": "x"}], 1),
            ([message("invalid", "x", 1)], 1),
            ([message("user", 1, 1)], 1),
            ([message("user", "x", True)], 1),
            ([message("user", "x", 0)], 1),
        )
        for messages, budget in invalid_calls:
            with self.subTest(messages=messages, budget=budget):
                with self.assertRaises(ValueError):
                    select_context_messages(messages, budget)

    def test_result_is_independent_and_input_is_not_mutated(self):
        messages = [message("user", "question", 1)]
        before = deepcopy(messages)

        result = select_context_messages(messages, 1)
        result[0]["content"] = "changed"

        self.assertEqual(messages, before)


if __name__ == "__main__":
    unittest.main()
