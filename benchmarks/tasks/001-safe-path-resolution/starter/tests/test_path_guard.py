from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from path_guard import resolve_workspace_path


class ResolveWorkspacePathTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.workspace = Path(self.temporary.name, "workspace")
        self.workspace.mkdir()

    def test_nested_path_is_allowed(self) -> None:
        resolved = resolve_workspace_path(self.workspace, "src/app.py")
        self.assertEqual(resolved, self.workspace / "src/app.py")

    def test_hidden_directory_is_preserved(self) -> None:
        resolved = resolve_workspace_path(
            self.workspace,
            ".github/workflows/ci.yml",
        )
        self.assertEqual(
            resolved,
            self.workspace / ".github/workflows/ci.yml",
        )

    def test_parent_traversal_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            resolve_workspace_path(self.workspace, "../private.py")

    def test_absolute_path_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            resolve_workspace_path(self.workspace, str(self.workspace.resolve()))

    def test_sibling_prefix_escape_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            resolve_workspace_path(self.workspace, "../workspace-evil/file.py")


if __name__ == "__main__":
    unittest.main()
