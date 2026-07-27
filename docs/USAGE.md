# Practical usage

Agent Scope Guard is a guardrail for AI-authored changes. It does not write
code or replace code review. It answers a narrower question: did a proposed
change stay inside the file boundaries that a human reviewed?

Choose the integration that matches the point where you want enforcement:

| When | Integration | Result |
| --- | --- | --- |
| While developing | Local CLI | Immediate scope feedback |
| Before committing | pre-commit hook | Rejects out-of-scope staged paths |
| On every pull request | GitHub Action | Required CI check for the Git diff |
| Before a sensitive next step | Human approval workflow | Freezes, reviews, and revalidates a proposal |

## 1. Install for local use

Python 3.11 or newer is required.

```bash
git clone https://github.com/altruylee/ai-coding-lab.git
cd ai-coding-lab
python -m pip install -e .
```

Create a repository policy:

```json
{
  "allowed_paths": ["src/**", "tests/**", "README.md"],
  "denied_paths": ["**/*.key", "**/*.pem", "**/*secret*"],
  "required_paths": ["tests/**"]
}
```

Check explicit paths:

```bash
agent-scope-guard check \
  --policy .github/agent-scope-policy.json \
  --changed-path src/example.py \
  --changed-path tests/test_example.py
```

Or check a Git range:

```bash
agent-scope-guard check \
  --policy .github/agent-scope-policy.json \
  --base-ref main \
  --head-ref HEAD
```

Exit code `0` means the proposal is in scope, `1` means a policy violation,
and `2` means the policy, input, or Git comparison is invalid.

`required_paths` applies to every evaluated proposal. Remove it when, for
example, documentation-only changes should not be required to touch tests.

## 2. Enforce scope in pull requests

Add a reviewed policy to the consuming repository, then add this step to a
`pull_request` workflow:

```yaml
- name: Enforce coding-agent scope
  uses: altruylee/ai-coding-lab@main
  with:
    policy: .github/agent-scope-policy.json
    base_ref: ${{ github.event.pull_request.base.sha }}
    head_ref: ${{ github.event.pull_request.head.sha }}
```

The checkout must use `fetch-depth: 0`. Grant the workflow only
`contents: read`. See the [complete GitHub Action guide](GITHUB_ACTION.md)
before using it in another repository.

## 3. Run the human approval gate

This repository includes a safe reference workflow. Open
[Human-approved agent execution](https://github.com/altruylee/ai-coding-lab/actions/workflows/human-approved-agent.yml),
select **Run workflow**, and use:

```text
branch: main
base_ref: HEAD^
policy: examples/approval-gate/policy.json
```

The first job resolves the commits, checks the changed paths, and uploads a
SHA-256-bound proposal. Inspect its job summary and artifact. The second job
waits at the `agent-approval` Environment until a reviewer selects
**Review deployments** and approves or rejects it.

After approval, a fresh job re-resolves the refs, recomputes the diff, checks
the policy and proposal digest again, and only then runs the fixed reference
checks.

The same workflow can be started with GitHub CLI:

```bash
gh workflow run human-approved-agent.yml \
  --repo altruylee/ai-coding-lab \
  --ref main \
  -f base_ref=HEAD^ \
  -f policy=examples/approval-gate/policy.json
```

The checked-in workflow runs tests and syntax compilation only. It does not
deploy, publish, write to a repository, or run an autonomous agent. Read the
[human approval workflow guide](HUMAN_APPROVAL_WORKFLOW.md) before adapting
the post-approval job to any operation with side effects.

## 4. Recommended AI coding workflow

1. A human defines the task and an allowed-path policy.
2. The coding agent works on a dedicated branch.
3. Run the local or pre-commit scope check.
4. Open a pull request and require the scope and test checks.
5. Review the diff and evidence; do not treat a passing scope check as a
   semantic code review.
6. For a sensitive next step, create an immutable proposal and require a
   separate human approval.
7. Record failures and rejected proposals as evidence, not only successes.

## 中文快速使用

Agent Scope Guard 不是写代码的 Agent，而是 AI Coding 的范围护栏。它用于
检查 AI 的改动是否停留在人工事先声明的文件边界内。

本地检查当前分支：

```powershell
cd D:\path\to\repository

agent-scope-guard check `
  --policy .github\agent-scope-policy.json `
  --base-ref main `
  --head-ref HEAD
```

日常推荐流程是：

```text
人工定义任务和文件边界
  -> AI 在独立分支修改
  -> Scope Guard 检查
  -> PR 自动测试
  -> 人工审查
  -> 必要时经过受保护环境批准后再执行敏感动作
```

当前仓库的人工审批示例只执行测试和语法检查，不会部署软件，也不会自动修改
GitHub 仓库。范围检查通过只说明“改动路径符合策略”，不代表代码逻辑一定正确。
