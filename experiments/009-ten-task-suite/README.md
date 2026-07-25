# Experiment 009 — Complete ten-task suite

## Question

Can the benchmark grow from three to ten synthetic repository tasks while
preserving a reproducible failing-starter/passing-reference boundary for every
new task?

## Added tasks

| Task | Capability |
| --- | --- |
| 004 | recursive configuration merge and deletion semantics |
| 005 | bounded exponential retry scheduling |
| 006 | untrusted archive path validation |
| 007 | recursive placeholder parsing and escaping |
| 008 | idempotent event deduplication and conflict detection |
| 009 | context-window selection under a token budget |
| 010 | non-overlapping text edits against original offsets |

All tasks use only synthetic data and the Python standard library. Each task
declares one editable candidate file.

## Reproduce

Run any task independently:

```bash
python -m benchmarks.runner \
  --task benchmarks/tasks/010-non-overlapping-text-edits \
  --output experiments/009-ten-task-suite/results-task010.json \
  --repo-root . \
  --verify
```

The Experiment 009 evidence manifest replays all seven new tasks and checks
Task 003 compatibility.

## Result

| Task | Starter | Reference | Benchmark valid |
| --- | --- | --- | --- |
| 004 | fail | pass | yes |
| 005 | fail | pass | yes |
| 006 | fail | pass | yes |
| 007 | fail | pass | yes |
| 008 | fail | pass | yes |
| 009 | fail | pass | yes |
| 010 | fail | pass | yes |

The public suite now contains ten tasks.

## What this proves

The repository has ten independently runnable task definitions covering
different failure modes. Every new starter exposes at least one tested defect,
and every checked-in reference satisfies the same public tests.

## What this does not prove

These are task-validation baselines, not model scores. Public tests cannot
measure hidden-test generalization, and the references must remain unavailable
to future blinded attempts.
