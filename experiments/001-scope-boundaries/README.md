# Experiment 001 ? Scope boundaries

## Question

Can Agent Scope Guard deterministically distinguish an allowed coding change
from three common failure modes?

1. a file outside the declared task scope;
2. a code change without a corresponding test change;
3. a sensitive key file, including one at the repository root.

## Inputs

- [`policy.json`](policy.json) declares allowed, denied, and required paths.
- [`cases.json`](cases.json) contains four synthetic changed-file sets and their
  expected violation codes.
- [`run.py`](run.py) evaluates every case with the public policy engine.

All paths and tasks are synthetic. No private repository data is used.

## Reproduce

From the repository root:

```bash
python experiments/001-scope-boundaries/run.py --verify
```

To regenerate the checked-in result after an intentional behavior change:

```bash
python experiments/001-scope-boundaries/run.py --write
```

The generated [`results.json`](results.json) contains no timestamp, machine
identifier, or network-derived field, so identical code and inputs produce an
identical artifact.

## Success criteria

- All four cases match their declared violation codes.
- The process exits with code `0`.
- The committed result is byte-for-byte equivalent to a fresh run.

## Limitations

This experiment tests policy evaluation, not an autonomous coding agent. It
does not yet measure whether an agent obeys the policy before writing files,
nor does it record tool calls, cost, latency, or human intervention.
