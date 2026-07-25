# Task 003 — Resolve task dependencies deterministically

Implement `resolve_task_order(tasks)` in `planner.py`.

The input maps task names to their direct dependencies. Return a valid
topological execution order.

## Requirements

- Accept a dictionary whose keys are non-empty task-name strings.
- Each dependency collection must be a list or tuple of task-name strings.
- Return every declared task exactly once.
- Place every dependency before the task that requires it.
- When multiple tasks are ready, choose the lexicographically smallest name.
- Ignore duplicate dependencies.
- Return `[]` for an empty task dictionary.
- Raise `ValueError` for:
  - invalid task names;
  - invalid dependency collections or names;
  - dependencies that are not declared tasks;
  - self-dependencies or longer dependency cycles.
- Produce deterministic errors and output independent of dictionary insertion
  order.
- Do not mutate the input.

Only `planner.py` may be changed.
