"""Resolve paths relative to a workspace."""

from pathlib import Path


def resolve_workspace_path(workspace: str | Path, relative_path: str) -> Path:
    """Return a resolved workspace path."""

    return (Path(workspace) / relative_path).resolve()
