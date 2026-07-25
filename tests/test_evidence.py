from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

from agent_scope_guard.evidence import (
    EvidenceError,
    build_evidence_bundle,
    resolve_repository_path,
    verify_evidence_bundle,
    write_evidence_bundle,
)


class EvidenceBundleTests(unittest.TestCase):
    def _workspace(
        self,
        directory: str,
        *,
        exit_code: int = 0,
    ) -> tuple[Path, Path]:
        root = Path(directory)
        policy_path = root / "policy.json"
        manifest_path = root / "manifest.json"
        policy_path.write_text(
            json.dumps(
                {
                    "allowed_paths": ["src/**", "tests/**"],
                    "required_paths": ["tests/**"],
                }
            ),
            encoding="utf-8",
        )
        manifest_path.write_text(
            json.dumps(
                {
                    "task_id": "test-task",
                    "policy_path": "policy.json",
                    "changed_paths": ["src/app.py", "tests/test_app.py"],
                    "checks": [
                        {
                            "name": "synthetic-check",
                            "command": [
                                sys.executable,
                                "-c",
                                f"print('checked'); raise SystemExit({exit_code})",
                            ],
                            "timeout_seconds": 10,
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        return root, manifest_path

    def test_bundle_passes_and_verifies(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root, manifest = self._workspace(directory)
            bundle = build_evidence_bundle(manifest, root)
            bundle_path = root / "evidence.json"
            write_evidence_bundle(bundle_path, bundle)

            self.assertTrue(bundle["summary"]["ok"])
            self.assertEqual(bundle["checks"][0]["exit_code"], 0)
            self.assertNotIn("stdout", bundle["checks"][0])
            self.assertNotIn("stderr", bundle["checks"][0])
            self.assertEqual(verify_evidence_bundle(bundle_path, root), ())

    def test_failed_check_marks_bundle_failed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root, manifest = self._workspace(directory, exit_code=3)
            bundle = build_evidence_bundle(manifest, root)

            self.assertFalse(bundle["summary"]["ok"])
            self.assertEqual(bundle["summary"]["checks_failed"], 1)
            self.assertEqual(bundle["checks"][0]["exit_code"], 3)

    def test_tampering_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root, manifest = self._workspace(directory)
            bundle = build_evidence_bundle(manifest, root)
            bundle["changed_paths"].append("src/hidden.py")
            bundle_path = root / "evidence.json"
            write_evidence_bundle(bundle_path, bundle)

            errors = verify_evidence_bundle(bundle_path, root)
            self.assertIn(
                "bundle_sha256 does not match bundle contents",
                errors,
            )

    def test_policy_change_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root, manifest = self._workspace(directory)
            bundle = build_evidence_bundle(manifest, root)
            bundle_path = root / "evidence.json"
            write_evidence_bundle(bundle_path, bundle)
            (root / "policy.json").write_text(
                json.dumps({"allowed_paths": ["**"]}),
                encoding="utf-8",
            )

            errors = verify_evidence_bundle(bundle_path, root)
            self.assertIn(
                "policy sha256 does not match current file",
                errors,
            )

    def test_output_path_cannot_escape_repository(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(EvidenceError, "outside the repository"):
                resolve_repository_path(directory, "../evidence.json", "output")


if __name__ == "__main__":
    unittest.main()
