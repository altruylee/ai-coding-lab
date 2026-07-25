# Experiment 004 — Agent attempt protocol

## Question

Can the lab reproduce a candidate solution while preserving enough provenance
to distinguish a real agent run from a test fixture?

## Method

The attempt runner reads a strict manifest, copies the task starter—but not the
reference—into a temporary workspace, overlays the candidate files, and runs
the task's declared checks. It records:

- task, candidate, and manifest hashes;
- candidate changed paths;
- disclosed agent, model, permissions, and network access;
- latency, token usage, cost, and human-intervention fields;
- commands, exit codes, timeout state, and pass/fail results.

Raw command output and hidden reasoning are not stored.

This experiment deliberately replays the known reference as a **fixture**. The
fixture proves the protocol can validate a solution, but its manifest discloses
reference access and therefore makes it ineligible for the public scoreboard.

## Reproduce

```bash
python -m benchmarks.attempts \
  --attempt benchmark_runs/fixtures/001-reference-replay/attempt.json \
  --output experiments/004-attempt-protocol/results.json \
  --repo-root . \
  --verify
```

## Result

- Candidate checks: passed.
- Provenance kind: fixture.
- Reference access: disclosed.
- Scoreboard eligibility: false.

## What this proves

The repository can replay a candidate overlay, enforce declared change paths,
and preserve missing metrics without inventing values.

## What this does not prove

No coding agent is credited with solving the task. The current session had
already seen the reference implementation, so presenting this replay as a blind
agent result would be invalid. The runner is also not an operating-system
sandbox. A later run must use a fresh, restricted agent context that can access
the starter and tests but not the reference directory, and independently attest
that boundary.
