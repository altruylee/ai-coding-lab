# Experiment 003 — Coding task baseline

## Question

Can the benchmark harness prove that a synthetic coding task is neither already
solved nor impossible?

The task asks a coding agent to reject workspace path escapes without breaking
valid hidden directories such as `.github`.

## Method

The runner creates two temporary workspaces:

1. **starter** — the intentionally incomplete implementation;
2. **reference** — the same starter with a known-good solution overlaid.

It executes the same declared tests in both workspaces. A valid task requires
the starter to fail and the reference to pass.

No task commands run in the checked-in source directories.

## Reproduce

```bash
python -m benchmarks.runner \
  --task benchmarks/tasks/001-safe-path-resolution \
  --output experiments/003-coding-task-baseline/results.json \
  --repo-root . \
  --verify
```

The checked-in [`results.json`](results.json) stores only commands, exit codes,
and pass/fail classification. It does not store raw test output.

## Result

- Starter state: expected failure observed.
- Reference state: expected success observed.
- Benchmark validity: passed.

## What this proves

The task has a measurable failing starting point and a reachable passing state.
It is suitable for later runs by real coding agents under controlled
permissions.

## What this does not prove

This is a task validation baseline, not a model leaderboard entry. No model
name, cost, latency, or autonomous success claim is attached to this result.
