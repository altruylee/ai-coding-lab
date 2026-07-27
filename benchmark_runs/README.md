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

| Task | Attempt | Configuration | Result | Elapsed | Human interventions |
| --- | --- | --- | --- | ---: | ---: |
| 002 | [`002-codex-blind-001`](agents/002-codex-blind-001/) | public test descriptions | pass | 195.648 s | 0 |
| 002 | [`002-codex-blind-002`](agents/002-codex-blind-002/) | public test descriptions | pass | 149.231 s | 0 |
| 002 | [`002-codex-spec-only-001`](agents/002-codex-spec-only-001/) | specification only | pass | 169.795 s | 0 |
| 002 | [`002-codex-spec-only-002`](agents/002-codex-spec-only-002/) | specification only | pass | 163.629 s | 0 |
| 006 | [`006-codex-spec-only-001`](agents/006-codex-spec-only-001/) | specification only | pass | 151.368 s | 0 |
| 006 | [`006-codex-public-tests-001`](agents/006-codex-public-tests-001/) | public test descriptions | pass | 179.320 s | 0 |
| 009 | [`009-codex-spec-only-001`](agents/009-codex-spec-only-001/) | specification only | fail | 182.647 s | 0 |
| 009 | [`009-codex-public-tests-001`](agents/009-codex-public-tests-001/) | public test descriptions | pass | 179.320 s | 0 |
| 010 | [`010-codex-spec-only-001`](agents/010-codex-spec-only-001/) | specification only | pass | 196.614 s | 0 |
| 010 | [`010-codex-public-tests-001`](agents/010-codex-public-tests-001/) | public test descriptions | pass | 205.559 s | 0 |
| 006 | [`006-codex-spec-only-002`](agents/006-codex-spec-only-002/) | specification only | pass | 166.603 s | 0 |
| 006 | [`006-codex-public-tests-002`](agents/006-codex-public-tests-002/) | public test descriptions | pass | 254.642 s | 0 |
| 009 | [`009-codex-spec-only-002`](agents/009-codex-spec-only-002/) | specification only | fail | 177.175 s | 0 |
| 009 | [`009-codex-public-tests-002`](agents/009-codex-public-tests-002/) | public test descriptions | pass | 254.642 s | 0 |
| 009 | [`009-codex-error-contract-001`](agents/009-codex-error-contract-001/) | clarified error contract; excluded from primary suite | pass | 204.532 s | 0 |
| 010 | [`010-codex-spec-only-002`](agents/010-codex-spec-only-002/) | specification only | pass | 204.532 s | 0 |
| 010 | [`010-codex-public-tests-002`](agents/010-codex-public-tests-002/) | public test descriptions | pass | 299.918 s | 0 |

All four runs used OpenAI Codex with the GPT-5 family disclosure. This is a run
log, not a model ranking. Token usage and cost were unavailable.

Campaign manifests group repeated attempts without deleting failures. See
[`task002-prompt-context-001`](campaigns/task002-prompt-context-001/campaign.json).
Multi-task suite manifests aggregate compatible campaigns while retaining every
task and attempt. See
[`first-multitask-prompt-context-001`](suites/first-multitask-prompt-context-001/suite.json).
The repeated primary comparison is
[`repeated-multitask-prompt-context-001`](suites/repeated-multitask-prompt-context-001/suite.json).
The clarified Task 009 run is retained but excluded because its prompt differs
from the declared primary configurations.

## Security boundary

Task checks execute candidate code. The attempt runner provides workspace
separation and file-overlay validation, not an operating-system sandbox. Review
task commands before running them, and use a container or restricted launcher
for untrusted community submissions. `reference_access` is disclosed
provenance; independent runners must enforce and attest that restriction.
