# Experiment 015: human-approval workflow

## Question

Can an agent proposal be validated automatically while preserving a real,
fail-closed human approval boundary before a second GitHub Actions job runs?

## Design

The experiment adds a manual reference workflow with two jobs:

1. resolve a fixed head commit, enforce scope, and upload a digested proposal;
2. wait on the protected `agent-approval` Environment, then download and
   independently revalidate the same-run artifact before running safe checks.

The first job also reads the public environment configuration and fails unless
required reviewers and custom deployment branch policies are present.
Deterministic local tests cover valid proposals, digest tampering, moving refs,
denied paths, unsafe policy paths, malformed proposal fields, environment
rules, workflow permissions, pinned actions, and the absence of
`pull_request_target`.

No private repository, employer data, credential, deployment, or external
mutation is used by the experiment fixtures.

## Success criteria

1. Valid unchanged proposals verify deterministically.
2. Tampered artifacts and moving revisions are rejected.
3. Scope violations cannot produce an approvable proposal.
4. Missing reviewers or open deployment branch policies fail closed.
5. The workflow uses a manual trigger, read-only token, fixed head SHA,
   non-persisted credentials, same-run artifact, and explicit Environment.
6. Repository tests and supported Python CI jobs remain green.

## Result

All deterministic scenarios pass. Experiment 015 records normalized output
hashes for the workflow verifier, syntax compilation, and Experiment 014
compatibility.

## Reproduce

```bash
python scripts/verify_approval_workflow.py
python -m unittest discover -s tests -p "test_approval.py" -v
python -m agent_scope_guard evidence \
  --manifest experiments/015-human-approval-workflow/manifest.json \
  --output experiments/015-human-approval-workflow/evidence.json \
  --repo-root . \
  --verify
```

## Limitations

- Local tests verify proposal and workflow behavior, not a human click in the
  hosted GitHub interface.
- Environment reviewer and branch rules are external repository settings.
- The reference post-approval action is intentionally limited to tests and
  compilation.
- A self-approved solo run is a deliberate pause, not independent review.
