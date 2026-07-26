# Experiment 010 — First multi-task blind campaign

## Question

Across three different task types, does adding descriptions of the public tests
change the observed success of isolated coding-agent attempts?

## Method

The campaign selected:

- Task 006: untrusted archive path validation;
- Task 009: AI context-window selection;
- Task 010: non-overlapping text edits.

Each task received two independent blind attempts:

1. task specification only;
2. the same specification plus descriptions of the public tests.

Each participant received a fresh context that did not inherit the authoring
conversation. It was instructed not to use tools, the filesystem, the network,
tests, or reference implementations. Returned candidates and attestations were
preserved without correction. The attempt runner then applied each candidate
to a temporary copy of the starter and executed the checked-in public tests.

## Reproduce

```bash
python -m benchmarks.suites \
  --suite benchmark_runs/suites/first-multitask-prompt-context-001/suite.json \
  --output experiments/010-first-multitask-blind-campaign/results.json \
  --repo-root . \
  --verify
```

## Results

| Task | Spec only | Public test descriptions |
| --- | --- | --- |
| 006 archive paths | pass | pass |
| 009 context window | fail | pass |
| 010 text edits | pass | pass |

Configuration summary:

| Configuration | Solved | Attempts | Raw elapsed milliseconds | Median |
| --- | ---: | ---: | --- | ---: |
| Spec only | 2 | 3 | 151368, 182647, 196614 | 182647 |
| Public test descriptions | 3 | 3 | 179320, 179320, 205559 | 179320 |

All six runs recorded zero human interventions. Provider token usage and cost
were unavailable and remain `null`.

## Failure classification

The Task 009 spec-only candidate implemented the selection algorithm but raised
`TypeError` for several invalid input types. The task required `ValueError` for
all invalid input, so the public validation correctly recorded a failure. The
candidate was not repaired or rerun. The public-test-description prompt stated
that exception expectation explicitly, and its candidate passed.

Classification: **contract mismatch — exception type**.

## Interpretation

This batch demonstrates that the repository can retain both passes and failures
across multiple tasks and aggregate compatible prompt configurations. It also
shows one concrete case where explicit test descriptions changed the observed
outcome.

## Limitations

- There is only one attempt per task and configuration.
- Tasks differ in difficulty, so the three results are not independent
  repetitions of one task.
- Public tests were used for validation; hidden-test generalization is not
  measured.
- All attempts disclose only the GPT-5 model family, not an exact deployment.
- `elapsed_ms` measures orchestrator wall-clock time from dispatch until the
  response was observed. Parallel scheduling and local orchestration can affect
  it.
- No statistical or stable success-rate claim is supported by six attempts.
