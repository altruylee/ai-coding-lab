from copy import deepcopy
import unittest

from archive_paths import normalize_archive_members


class ArchivePathTests(unittest.TestCase):
    def test_normalizes_and_sorts_safe_names(self):
        names = [
            "src\\agent.py",
            "docs//guide.md",
            "./tests/./test_agent.py",
        ]

        self.assertEqual(
            normalize_archive_members(names),
            ["docs/guide.md", "src/agent.py", "tests/test_agent.py"],
        )

    def test_rejects_parent_segments_even_if_they_cancel(self):
        unsafe = (
            "../secret.txt",
            "safe/../../secret.txt",
            "safe/../secret.txt",
            "..\\secret.txt",
        )
        for name in unsafe:
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    normalize_archive_members([name])

    def test_rejects_absolute_unc_and_drive_paths(self):
        unsafe = (
            "/etc/passwd",
            "\\\\server\\share\\file.txt",
            "C:\\Windows\\file.txt",
            "d:/data.txt",
        )
        for name in unsafe:
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    normalize_archive_members([name])

    def test_rejects_nul_empty_and_normalized_empty_names(self):
        for name in ("", ".", "./", "///", "safe\x00.txt"):
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    normalize_archive_members([name])

    def test_rejects_case_insensitive_duplicates(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            normalize_archive_members(["src/Agent.py", "src\\agent.py"])

    def test_invalid_collection_and_elements_are_rejected(self):
        invalid = ("src/file.py", None, [1])
        for value in invalid:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    normalize_archive_members(value)

    def test_input_is_not_mutated(self):
        names = ["b/file.py", "a/file.py"]
        before = deepcopy(names)

        normalize_archive_members(names)

        self.assertEqual(names, before)


if __name__ == "__main__":
    unittest.main()
