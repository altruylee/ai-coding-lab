# pre-commit integration

Agent Scope Guard can run before each Git commit. The pre-commit framework
installs this repository in an isolated Python environment and passes staged
file paths to the hook. The hook does not read file contents or contact a
network service while it runs.

## 1. Add a policy

Copy [`examples/pre-commit/policy.json`](../examples/pre-commit/policy.json) to
`.github/agent-scope-policy.json`, then replace the example paths with the
repository's reviewed boundaries.

`required_paths` can enforce rules such as “a staged source change must include
a staged test”. Remove that field when the rule does not fit the repository.

## 2. Configure pre-commit

Merge this entry into `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/altruylee/ai-coding-lab
    rev: main
    hooks:
      - id: agent-scope-guard
        args:
          - --policy
          - .github/agent-scope-policy.json
```

The example uses `main` until the first stable hook release. Production users
should replace it with a reviewed tag or full commit SHA.

Install and run the hook:

```bash
python -m pip install pre-commit
pre-commit install
pre-commit run agent-scope-guard
```

pre-commit is an integration dependency for the consuming repository. It is
not a runtime dependency of Agent Scope Guard.

## Exit behavior

- `0`: every supplied staged path satisfies the policy;
- `1`: at least one scope rule is violated;
- `2`: the hook input or policy is invalid.

The default policy path is `.agent-scope-guard.json`. Configure `--policy` when
the repository stores the policy elsewhere. Add `--format json` to the hook's
`args` when machine-readable output is preferred.

## Behavior and limitations

The normal pre-commit stage supplies added, copied, modified, renamed,
type-changed, unmerged, and unknown staged paths. Deleted paths are excluded by
pre-commit's default Git filter, and rename checks observe the destination path;
dedicated rename and deletion policies remain planned work.

`pre-commit run --all-files` supplies every matching tracked file, not only
staged changes. That mode is useful for policy audits but should not be
interpreted as a staged-change result. A normal `git commit` or
`pre-commit run agent-scope-guard --files ...` preserves change-focused
semantics.

This hook controls path scope only. It does not inspect code semantics, execute
tests, approve a commit, or prove that a change was authored by an AI agent.
