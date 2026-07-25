# Experiment 005 — Nested secret redaction task

## Question

Can the benchmark represent a privacy-focused coding task where a plausible
shallow implementation fails but a recursive implementation passes?

## Method

Task 002 models agent telemetry containing nested tool arguments and HTTP
headers. The implementation must:

- redact values under exact normalized sensitive keys;
- traverse dictionaries, lists, and tuples;
- preserve partial key matches;
- preserve container types;
- avoid mutating the original value.

The runner executes the same public tests against the incomplete starter and a
known-good reference overlay in separate temporary workspaces.

## Reproduce

```bash
python -m benchmarks.runner \
  --task benchmarks/tasks/002-nested-secret-redaction \
  --output experiments/005-secret-redaction-task/results.json \
  --repo-root . \
  --verify
```

## Result

- Starter state: expected failure observed.
- Reference state: expected success observed.
- Benchmark validity: passed.

## What this proves

The task is neither already solved nor impossible, has a single declared
candidate file, and can be reproduced without private data or external
dependencies.

## What this does not prove

This baseline is not an agent attempt or leaderboard result. The reference is
checked in for task validation and must be hidden from any later blinded agent
run.
