# Experiment 008 — Deterministic dependency-order task

## Question

Can the benchmark represent a graph-planning task where a plausible
direct-dependency implementation fails but a deterministic topological
implementation passes?

## Method

Task 003 models a small build planner. The implementation must:

- place all transitive dependencies before their dependents;
- choose the lexicographically smallest ready task;
- reject unknown dependencies and cycles deterministically;
- validate input shapes and names;
- ignore duplicate dependencies without mutating the input.

The runner executes the same public tests against the incomplete starter and a
known-good reference overlay in separate temporary workspaces.

## Reproduce

```bash
python -m benchmarks.runner \
  --task benchmarks/tasks/003-deterministic-dependency-order \
  --output experiments/008-deterministic-dependency-task/results.json \
  --repo-root . \
  --verify
```

## Result

- Starter state: expected failure observed.
- Reference state: expected success observed.
- Benchmark validity: passed.

## What this proves

The task has a reproducible failure/success boundary, a single declared
candidate file, and no dependency on private data or third-party packages.

## What this does not prove

This baseline is not an agent attempt or leaderboard result. The checked-in
reference validates the task and must be hidden from later blinded runs.
