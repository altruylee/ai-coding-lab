# Experiment 011 — Repeated multi-task campaign

## Question

Do the prompt-context outcomes from Experiment 010 persist after one
additional independent attempt per task and configuration?

## Method

Tasks 006, 009, and 010 each have two specification-only attempts and two
attempts with public test descriptions. The new campaign manifests include all
12 primary attempts while leaving Experiment 010 and its original manifests
unchanged.

One Task 009 run accidentally received an extra sentence requiring
`ValueError` for every invalid input. It is preserved as
`009-codex-error-contract-001`, validated independently, and excluded from the
primary repeated suite because its prompt is not the declared spec-only
configuration.

## Reproduce

```bash
python -m benchmarks.suites \
  --suite benchmark_runs/suites/repeated-multitask-prompt-context-001/suite.json \
  --output experiments/011-repeated-multitask-campaign/results.json \
  --repo-root . \
  --verify
```

## Primary results

| Task | Spec only | Public test descriptions |
| --- | ---: | ---: |
| 006 archive paths | 2/2 | 2/2 |
| 009 context window | 0/2 | 2/2 |
| 010 text edits | 2/2 | 2/2 |
| **Total** | **4/6** | **6/6** |

Raw elapsed values:

| Configuration | Milliseconds | Median |
| --- | --- | ---: |
| Spec only | 151368, 166603, 182647, 177175, 196614, 204532 | 179911 |
| Public test descriptions | 179320, 254642, 179320, 254642, 205559, 299918 | 230100.5 |

All 12 primary attempts recorded zero human interventions. Provider token and
cost data remain unavailable.

## Protocol deviation result

The extra Task 009 error-contract run passed. Both exact specification-only
Task 009 attempts failed in the same way: they used `TypeError` for type
mismatches, while the public tests require `ValueError`. Both public-test-
description attempts passed.

This is evidence of a **specification/test contract gap**, not clean evidence
that test descriptions generally improve coding ability. The public test
descriptions disclose an exception-type requirement that the specification-
only prompt does not state for every invalid input.

## Interpretation

The repeated batch confirms that the outcome is task-local:

- Tasks 006 and 010 passed under both prompt configurations.
- Task 009 changed outcome when the exception contract became explicit.
- The protocol-deviation run isolates that contract sentence as a plausible
  explanation.

## Limitations

- Two attempts per task and configuration remain a small sample.
- Public tests are visible descriptions, not hidden generalization checks.
- The exact GPT-5 deployment is not exposed.
- Wall-clock elapsed time includes parallel scheduling and orchestrator delay.
- Tasks are maintainer-selected and differ in difficulty.
- The evidence supports observed counts only, not stable reliability rates or
  model superiority.

See [Threats to validity](../../docs/THREATS_TO_VALIDITY.md) for the repository-
wide interpretation boundary.
