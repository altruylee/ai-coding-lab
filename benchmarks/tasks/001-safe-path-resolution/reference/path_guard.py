"""Resolve paths relative to a workspace."""

import os
from pathlib import Path


def resolve_workspace_path(workspace: str | Path, relative_path: str) -> Path:
    """Resolve a non-empty relative path that stays inside the workspace."""

    if not isinstance(relative_path, str) or not relative_path.strip():
        raise ValueError("relative_path must be a non-empty string")

    relative = Path(relative_path)
    if relative.is_absolute():
        raise ValueError("absolute paths are not allowed")

    root = Path(workspace).resolve()
    candidate = (root / relative).resolve()
    try:
        common = Path(os.path.commonpath((root, candidate)))
    except ValueError as exc:
        raise ValueError("path is outside the workspace") from exc
    if common != root:
        raise ValueError("path is outside the workspace")
    return candidate
