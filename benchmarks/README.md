# Coding-agent benchmarks

Each task is a self-contained, synthetic repository challenge with:

- a human-readable `TASK.md`;
- a machine-readable `task.json`;
- a failing `starter/` workspace;
- a passing `reference/` overlay;
- deterministic validation commands.

Tasks also declare `candidate_paths`. Recorded attempts are rejected when their
candidate overlay changes tests or any other undeclared file.

The runner copies task files into a temporary directory before executing
commands. It does not modify the checked-in starter or reference files.

Task commands are executable instructions. Review `task.json` before running a
task, just as you would review a script or CI workflow.

## Run a task

```bash
python -m benchmarks.runner \
  --task benchmarks/tasks/001-safe-path-resolution \
  --output experiments/003-coding-task-baseline/results.json \
  --verify
```

A valid benchmark must demonstrate both sides:

1. the starter state produces the declared failing outcome;
2. the reference overlay produces the declared passing outcome.

This validates the task itself. It does not claim that a particular model or
agent solved the task.

## Replay a recorded attempt

```bash
python -m benchmarks.attempts \
  --attempt benchmark_runs/fixtures/001-reference-replay/attempt.json \
  --output experiments/004-attempt-protocol/results.json \
  --repo-root . \
  --verify
```

Attempt manifests distinguish real agent runs from human submissions and
protocol fixtures. Passing checks alone does not make a run
scoreboard-eligible; see [`benchmark_runs/README.md`](../benchmark_runs/README.md).
