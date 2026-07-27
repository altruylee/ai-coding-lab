# Experiment 012: reusable GitHub Action integration

## Question

Can Agent Scope Guard be called as a composite GitHub Action while preserving
its existing exit codes and detecting both allowed and denied pull-request
changes?

## Design

The integration adds:

- a root `action.yml` with four explicit inputs;
- a small Python entry point that translates Action inputs to the existing CLI;
- a copyable pull-request workflow and policy;
- a deterministic verifier that creates two temporary synthetic Git
  repositories.

The first repository changes an allowed source file and adds a required test.
The second adds a synthetic `deploy.key` path. No secret value, private
repository content, network call, or employer data is used.

## Success criteria

1. The allowed source-and-test change returns exit code `0`.
2. The denied key-file change returns exit code `1` with `denied_path`.
3. Missing or invalid Action inputs return exit code `2`.
4. The full repository test suite and Python compilation pass.
5. CI exercises the repository itself through `uses: ./`.

## Result

All deterministic integration scenarios and local tests pass. The checked-in
evidence bundle records the verifier and compilation results without retaining
raw command output.

## Reproduce

```bash
python scripts/verify_github_action.py
python -m unittest discover -s tests -p "test_github_action.py" -v
python -m agent_scope_guard evidence \
  --manifest experiments/012-github-action-integration/manifest.json \
  --output experiments/012-github-action-integration/evidence.json \
  --repo-root . \
  --verify
```

## Limitations

- The verifier models GitHub's checkout locally; GitHub-hosted runner behavior
  is additionally covered by CI after publication.
- The example initially references `main`; security-sensitive consumers should
  pin a reviewed full commit SHA.
- The action enforces file boundaries, not code correctness or command safety.
- Rename and deletion policies remain future work.
