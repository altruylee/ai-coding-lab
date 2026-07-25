# Experiment 002 ? Task evidence bundle

## Question

Can a coding task produce a machine-readable record that proves:

- which repository paths were declared as changed;
- which scope policy was evaluated;
- which verification commands actually ran;
- whether each command passed, failed, or timed out;
- whether the record or its referenced inputs were modified later?

## Privacy model

The bundle intentionally does **not** store command stdout or stderr. It stores
only normalized SHA-256 hashes of those streams, the command array, exit code,
timeout state, and pass/fail status. This allows comparison without publishing
logs that may contain private paths, source snippets, or credentials.

Commands in a manifest are executable instructions. Review a manifest before
running it, just as you would review a script or CI workflow.

## Inputs and output

- [`manifest.json`](manifest.json) declares the task paths and two deterministic
  verification commands.
- [`policy.json`](policy.json) defines the permitted public repository scope.
- [`evidence.json`](evidence.json) is the generated evidence bundle.

All inputs are synthetic or belong to this public repository.

## Reproduce

From the repository root:

```bash
python -m agent_scope_guard evidence \
  --manifest experiments/002-task-evidence/manifest.json \
  --output experiments/002-task-evidence/evidence.json \
  --repo-root . \
  --verify
```

Verify integrity without executing the manifest commands:

```bash
python -m agent_scope_guard verify-evidence \
  --bundle experiments/002-task-evidence/evidence.json \
  --repo-root .
```

## Success criteria

- The declared scope has no violations.
- Both verification commands exit successfully.
- A fresh run matches the committed evidence byte for byte.
- Integrity verification confirms the bundle, manifest, and policy hashes.
- Changing any recorded field causes verification to fail.

## Limitations

The bundle proves what this runner observed; it does not prove that no other
commands ran outside the runner. Stronger provenance will require an isolated
execution environment, signed attestations, or CI-native identity.
