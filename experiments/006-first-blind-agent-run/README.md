# Experiment 006 — First blind agent run

## Question

Can an isolated coding agent solve Task 002 from the task statement and public
test descriptions without receiving the reference implementation?

## Method

An independent Codex sub-agent was started with no inherited conversation
context. Its complete input is checked in as
[`PROMPT.md`](../../benchmark_runs/agents/002-codex-blind-001/PROMPT.md).

The prompt prohibited tools, filesystem access, network access, and seeking the
reference. The agent returned only a candidate `redactor.py` and the required
attestation. The orchestrator:

1. sent no follow-up messages;
2. preserved the returned code without correction;
3. measured wall-clock time from dispatch to received response;
4. replayed the candidate through the standard attempt runner.

## Reproduce

```bash
python -m benchmarks.attempts \
  --attempt benchmark_runs/agents/002-codex-blind-001/attempt.json \
  --output experiments/006-first-blind-agent-run/results.json \
  --repo-root . \
  --verify
```

## Result

- Agent: OpenAI Codex.
- Model disclosure: GPT-5 family; exact deployment was not exposed.
- Candidate checks: passed.
- Wall-clock elapsed time: 195,648 ms.
- Human interventions: 0.
- Reference access: declared false.
- Token usage and cost: unavailable, preserved as `null`.
- Scoreboard eligibility under protocol v1: true.

## What this proves

The repository can record and reproduce a real candidate from a fresh agent
context, preserve unavailable metrics honestly, and distinguish the attempt
from reference-replay fixtures.

## Limitations

- This is one run, not a model comparison or stable success-rate estimate.
- The tests were public; there was no hidden test set.
- The exact model deployment, token usage, and cost were not exposed.
- The no-tool boundary was prompt-enforced and attested, not enforced by an
  operating-system container.
- Wall-clock time includes orchestration and scheduling overhead.
- The attestation and candidate provenance are reviewable claims, not
  cryptographic proof.
