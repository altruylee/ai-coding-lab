from copy import deepcopy
import unittest

from text_edits import apply_text_edits


class TextEditTests(unittest.TestCase):
    def test_applies_unordered_edits_against_original_offsets(self):
        source = "alpha beta gamma"
        edits = [
            {"start": 11, "end": 16, "text": "G"},
            {"start": 0, "end": 5, "text": "A"},
            {"start": 6, "end": 10, "text": "BETA"},
        ]

        self.assertEqual(apply_text_edits(source, edits), "A BETA G")

    def test_supports_deletion_replacement_and_insertion(self):
        source = "abcdef"
        edits = [
            {"start": 1, "end": 3, "text": ""},
            {"start": 3, "end": 5, "text": "XY"},
            {"start": 6, "end": 6, "text": "!"},
        ]

        self.assertEqual(apply_text_edits(source, edits), "aXYf!")

    def test_adjacent_edits_and_boundary_insertions_are_allowed(self):
        source = "abcd"
        edits = [
            {"start": 0, "end": 2, "text": "A"},
            {"start": 2, "end": 2, "text": "-"},
            {"start": 2, "end": 4, "text": "B"},
        ]

        self.assertEqual(apply_text_edits(source, edits), "A-B")

    def test_overlaps_and_duplicate_insertions_are_rejected(self):
        invalid = (
            [
                {"start": 0, "end": 3, "text": "x"},
                {"start": 2, "end": 4, "text": "y"},
            ],
            [
                {"start": 1, "end": 1, "text": "x"},
                {"start": 1, "end": 1, "text": "y"},
            ],
        )
        for edits in invalid:
            with self.subTest(edits=edits):
                with self.assertRaises(ValueError):
                    apply_text_edits("abcd", edits)

    def test_invalid_shapes_offsets_and_types_are_rejected(self):
        invalid_calls = (
            (None, []),
            ("abc", None),
            ("abc", [{"start": 0, "end": 1}]),
            ("abc", [{"start": 0, "end": 1, "text": "x", "extra": 1}]),
            ("abc", [{"start": True, "end": 1, "text": "x"}]),
            ("abc", [{"start": -1, "end": 1, "text": "x"}]),
            ("abc", [{"start": 2, "end": 1, "text": "x"}]),
            ("abc", [{"start": 0, "end": 4, "text": "x"}]),
            ("abc", [{"start": 0, "end": 1, "text": 1}]),
        )
        for source, edits in invalid_calls:
            with self.subTest(source=source, edits=edits):
                with self.assertRaises(ValueError):
                    apply_text_edits(source, edits)

    def test_empty_edits_and_input_immutability(self):
        edits = [{"start": 0, "end": 1, "text": "A"}]
        before = deepcopy(edits)

        self.assertEqual(apply_text_edits("abc", []), "abc")
        apply_text_edits("abc", edits)

        self.assertEqual(edits, before)


if __name__ == "__main__":
    unittest.main()
