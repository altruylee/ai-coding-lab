# GitHub Action integration

Agent Scope Guard can run as a composite GitHub Action and fail a pull request
when its changed files leave a reviewed policy boundary. The action reads the
local checkout and Git history only. It does not upload repository contents or
require a token.

## 1. Add a policy

Copy [`examples/github-actions/policy.json`](../examples/github-actions/policy.json)
to `.github/agent-scope-policy.json` in the repository that will use the action,
then replace the example paths with that repository's boundaries.

```json
{
  "allowed_paths": ["src/**", "tests/**", "README.md"],
  "denied_paths": ["**/*.key", "**/*.pem"],
  "required_paths": ["tests/**"]
}
```

`required_paths` is useful when every agent-authored code change must include a
test. Remove it when that rule does not fit the repository.

## 2. Add the workflow

Copy [`examples/github-actions/scope-check.yml`](../examples/github-actions/scope-check.yml)
to `.github/workflows/agent-scope.yml`.

The important details are:

- use `pull_request`, not `pull_request_target`, for untrusted contributions;
- set `fetch-depth: 0` so both compared commits are available;
- grant only `contents: read`;
- set `base_ref` and `head_ref` to the pull request commit SHAs;
- pin third-party actions to full commit SHAs in security-sensitive repositories.

The example uses `altruylee/ai-coding-lab@main` so it works before the first
stable action release. Production users should replace `main` with a reviewed
full commit SHA.

## Inputs and exit behavior

| Input | Required | Default | Meaning |
| --- | --- | --- | --- |
| `policy` | yes | none | Repository-relative JSON policy path |
| `base_ref` | yes | none | Merge-base side of the Git comparison |
| `head_ref` | no | `HEAD` | Revision containing proposed changes |
| `output_format` | no | `text` | `text` or `json` |

The action returns:

- `0` when every changed path satisfies the policy;
- `1` when a scope violation is found;
- `2` for invalid inputs, policies, or Git comparisons.

## Threat model and limitations

This integration controls changed-file scope. It does not inspect source
semantics, sandbox commands, approve a pull request, or prove that an author is
an AI agent. Rename and deletion policy support is still planned; the current
Git comparison covers added, copied, modified, and renamed destination paths.

The action requires Python 3.11 or newer and a Git checkout containing both
revisions. It uses the repository's existing shell and Python installation and
has no runtime dependency outside the Python standard library.
