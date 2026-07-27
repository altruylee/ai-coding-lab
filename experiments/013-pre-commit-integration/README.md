# Experiment 013: pre-commit staged-path integration

## Question

Can Agent Scope Guard enforce the same path policy before a local Git commit,
using only filenames supplied by the pre-commit framework?

## Design

The integration publishes a standard `.pre-commit-hooks.yaml` manifest and a
Python console entry point. A deterministic verifier exercises four synthetic
inputs:

1. an allowed source file plus its required test;
2. a denied synthetic `deploy.key` path;
3. a source file missing a required test path;
4. a policy path attempting to escape the repository.

No private repository, real key value, network request, or employer data is
used.

## Success criteria

1. Allowed staged paths return exit code `0`.
2. Denied or incomplete staged paths return exit code `1` with the expected
   violation classification.
3. An escaping policy path returns exit code `2`.
4. The hook manifest and packaged console entry point agree.
5. The full repository test suite and CI remain green.

## Result

All deterministic scenarios pass. Experiment 013 records hashed command output
for the verifier, syntax compilation, and Experiment 012 compatibility.

## Reproduce

```bash
python scripts/verify_pre_commit.py
python -m unittest discover -s tests -p "test_pre_commit.py" -v
python -m agent_scope_guard evidence \
  --manifest experiments/013-pre-commit-integration/manifest.json \
  --output experiments/013-pre-commit-integration/evidence.json \
  --repo-root . \
  --verify
```

## Limitations

- The deterministic verifier calls the packaged module without installing the
  external pre-commit framework; hosted CI validates the same entry point on
  all supported Python versions.
- `--all-files` represents a repository audit, not staged-change scope.
- Deleted paths and rename source paths are not supplied by pre-commit's
  default filter.
- The hook enforces paths, not source semantics or test correctness.
