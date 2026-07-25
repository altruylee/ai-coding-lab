# Task — Safe workspace path resolution

Implement `resolve_workspace_path()` in `path_guard.py`.

Requirements:

1. Accept a workspace directory and a non-empty relative path.
2. Return the resolved path when it stays inside the workspace.
3. Preserve valid hidden path components such as `.github`.
4. Reject absolute paths.
5. Reject `..` traversal and sibling-prefix escapes.
6. Raise `ValueError` for invalid input.

Only modify `path_guard.py` and tests when necessary. Run:

```bash
python -m unittest discover -s tests -v
```

The task is synthetic and contains no private project material.
