# Recorded benchmark attempts

Each attempt stores:

- an `attempt.json` provenance manifest;
- a candidate file overlay;
- optional hashed prompt and attestation artifacts;
- deterministic validation results in a versioned experiment.

Candidate overlays are applied to a temporary copy of the task starter. The
reference is not copied into that workspace. Tasks declare `candidate_paths`,
and an attempt is rejected if its overlay changes tests or any other undeclared
path.

An attempt is scoreboard-eligible only when it:

1. identifies itself as an agent run;
2. discloses the agent and model;
3. states that the reference was not accessible;
4. records latency, permissions, network access, and human interventions;
5. passes the task's deterministic checks.

Token and cost fields may be `null` when the provider does not expose them. The
result preserves that missing-data state instead of estimating values.

The `fixtures/` directory tests this protocol. Fixtures are never leaderboard
entries, even when their candidate code passes.

## Recorded agent runs

| Task | Attempt | Agent/model | Result | Elapsed | Human interventions |
| --- | --- | --- | --- | ---: | ---: |
| 002 | [`002-codex-blind-001`](agents/002-codex-blind-001/) | OpenAI Codex / GPT-5 family | pass | 195.648 s | 0 |

This is a run log, not a model ranking. Token usage and cost were unavailable
for the first run.

## Security boundary

Task checks execute candidate code. The attempt runner provides workspace
separation and file-overlay validation, not an operating-system sandbox. Review
task commands before running them, and use a container or restricted launcher
for untrusted community submissions. `reference_access` is disclosed
provenance; independent runners must enforce and attest that restriction.
