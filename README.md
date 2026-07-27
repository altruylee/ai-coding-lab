# AI Coding Reliability Lab

[![CI](https://github.com/altruylee/ai-coding-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/altruylee/ai-coding-lab/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Small, reproducible experiments for making coding agents safer, more
measurable, and easier to trust in real repositories.

The lab starts with **Agent Scope Guard**, a zero-dependency Python tool that
checks whether an AI coding change stayed inside its declared file boundaries.

## Why this exists

Coding agents are increasingly capable, but a successful demo is not the same
as a reliable engineering workflow. Real repositories need explicit scope,
automated verification, reviewable evidence, and safe failure modes.

This repository focuses on those missing pieces:

- scope control;
- reproducible agent tasks;
- evaluation instead of anecdotes;
- human approval at meaningful boundaries;
- small tools that work in ordinary CI.

## Agent Scope Guard

Create a policy:

```json
{
  "allowed_paths": [
    "agent_scope_guard/**",
    "tests/**",
    "README.md"
  ],
  "denied_paths": [
    ".github/workflows/release.yml",
    "**/*.pem",
    "**/*.key"
  ],
  "required_paths": [
    "tests/**"
  ]
}
```

Check an explicit set of changed files:

```bash
python -m agent_scope_guard check \
  --policy examples/policy.json \
  --changed-path agent_scope_guard/cli.py \
  --changed-path tests/test_policy.py
```

Or check a Git diff:

```bash
python -m agent_scope_guard check \
  --policy examples/policy.json \
  --base-ref main \
  --head-ref HEAD
```

A successful check exits with code `0`. A scope violation exits with code `1`
and explains which rule failed. Invalid configuration or Git errors exit with
code `2`.

## GitHub Action

Use Agent Scope Guard directly in a pull-request workflow:

```yaml
- name: Enforce coding-agent scope
  uses: altruylee/ai-coding-lab@main
  with:
    policy: .github/agent-scope-policy.json
    base_ref: ${{ github.event.pull_request.base.sha }}
    head_ref: ${{ github.event.pull_request.head.sha }}
```

The checkout must include both revisions (`fetch-depth: 0`). See the
[complete GitHub Action guide](docs/GITHUB_ACTION.md) for the policy, workflow,
least-privilege permissions, commit-pinning guidance, and limitations.

## pre-commit hook

Catch scope violations before a commit leaves the developer's machine:

```yaml
repos:
  - repo: https://github.com/altruylee/ai-coding-lab
    rev: main
    hooks:
      - id: agent-scope-guard
        args: [--policy, .github/agent-scope-policy.json]
```

See the [pre-commit integration guide](docs/PRE_COMMIT.md) for installation,
pinning guidance, staged-file semantics, and known rename/deletion limits.

## MCP adapter

Give an MCP-capable coding agent a read-only scope check before it edits or
proposes a change:

```json
{
  "mcpServers": {
    "agent-scope-guard": {
      "command": "agent-scope-guard-mcp",
      "args": ["--repo-root", "/absolute/path/to/repository"]
    }
  }
}
```

The adapter exposes explicit-path and local Git-diff tools. It reads only the
selected policy and Git path names; it does not read source contents, access
the network, mutate files, or replace human approval. See the
[MCP adapter guide](docs/MCP_ADAPTER.md) for installation, tool contracts,
safety boundaries, and protocol limitations.

## Human approval gate

The manual reference workflow validates and freezes an agent proposal before a
protected GitHub Environment pauses the execution job for a human decision.
After approval, a fresh job re-resolves the commits, recomputes the diff, and
rejects any proposal mismatch before running the approved checks.

The workflow is read-only by default, pins official Actions to full commit
SHAs, does not accept arbitrary commands, and fails unless `agent-approval` has
required reviewers and a custom deployment branch policy. See the
[human approval workflow guide](docs/HUMAN_APPROVAL_WORKFLOW.md) for mandatory
repository settings, operation, threat boundaries, and limitations.

## Task evidence bundles

Version 0.2.0 can run verification commands declared in a reviewed manifest
and create a privacy-conscious evidence bundle:

```bash
python -m agent_scope_guard evidence \
  --manifest experiments/002-task-evidence/manifest.json \
  --output experiments/002-task-evidence/evidence.json \
  --repo-root .
```

The bundle records scope results, command arrays, exit codes, timeout status,
and normalized output hashes. It does not store raw command output. Verify a
bundle without executing its commands:

```bash
python -m agent_scope_guard verify-evidence \
  --bundle experiments/002-task-evidence/evidence.json \
  --repo-root .
```

## Local verification

```bash
python -m unittest discover -s tests -v
python -m compileall -q agent_scope_guard tests
```

The project uses only the Python standard library at runtime.

## Reproducible experiments

Experiment 001 checks four synthetic scope scenarios and commits a deterministic
evidence artifact:

```bash
python experiments/001-scope-boundaries/run.py --verify
```

Read [Experiment 001 — Scope boundaries](experiments/001-scope-boundaries/README.md)
for the question, inputs, success criteria, result, and limitations.

[Experiment 002 — Task evidence bundle](experiments/002-task-evidence/README.md)
adds verifiable scope, command, output-hash, and integrity evidence.

[Experiment 003 — Coding task baseline](experiments/003-coding-task-baseline/README.md)
adds a synthetic repository task, temporary-workspace runner, failing starter,
passing reference, and deterministic validation result.

[Experiment 004 — Agent attempt protocol](experiments/004-attempt-protocol/README.md)
adds provenance-aware candidate replay, declared change boundaries, metric
fields, and explicit scoreboard eligibility.

[Experiment 005 — Nested secret redaction task](experiments/005-secret-redaction-task/README.md)
adds a second synthetic task covering privacy-safe agent telemetry.

[Experiment 006 — First blind agent run](experiments/006-first-blind-agent-run/README.md)
records the first provenance-aware agent candidate, including latency,
intervention count, missing usage data, attestation, and limitations.

[Experiment 007 — Prompt-context comparison campaign](experiments/007-prompt-context-campaign/README.md)
compares two prompt configurations with two blinded attempts each.

[Experiment 008 — Deterministic dependency-order task](experiments/008-deterministic-dependency-task/README.md)
adds a graph-planning challenge with stable ordering and deterministic errors.

[Experiment 009 — Complete ten-task suite](experiments/009-ten-task-suite/README.md)
expands the benchmark to ten diverse, independently reproducible tasks.

[Experiment 010 — First multi-task blind campaign](experiments/010-first-multitask-blind-campaign/README.md)
records six isolated attempts across three tasks and preserves one real failure.

[Experiment 011 — Repeated multi-task campaign](experiments/011-repeated-multitask-campaign/README.md)
expands the comparison to 12 primary attempts and isolates a prompt-contract
confound.

[Experiment 012 — GitHub Action integration](experiments/012-github-action-integration/README.md)
turns the scope checker into a reusable pull-request guard and validates it
against allowed and denied synthetic Git histories.

[Experiment 013 — pre-commit integration](experiments/013-pre-commit-integration/README.md)
adds a packaged staged-path hook and verifies allowed, denied, incomplete, and
unsafe configurations.

[Experiment 014 — MCP scope adapter](experiments/014-mcp-scope-adapter/README.md)
adds two read-only MCP tools and verifies protocol framing, explicit paths,
local Git diffs, policy violations, and unsafe configuration failures.

[Experiment 015 — Human approval workflow](experiments/015-human-approval-workflow/README.md)
adds a fail-closed Environment gate, immutable proposal handoff, ref
revalidation, and least-privilege reference execution.

## Repository map

```text
agent_scope_guard/   Scope policy engine and command-line interface
action.yml           Reusable composite GitHub Action
benchmarks/          Synthetic coding-agent tasks and isolated runner
benchmark_runs/      Candidate overlays and provenance manifests
examples/            Reproducible example policies
experiments/         Versioned experiments and evidence artifacts
tests/               Unit and CLI tests
docs/                Roadmap and experiment protocol
.github/workflows/   Continuous integration
```

## Lab principles

1. Publish code and evidence, not predictions.
2. Prefer a small reproducible result over a large unverified claim.
3. Record failure modes as carefully as successful cases.
4. Use synthetic or public repositories only.
5. Never derive public artifacts from private employer code or data.

## Roadmap

The first milestones are:

- file-scope enforcement;
- command and test evidence;
- a reusable coding-agent task format;
- a small public benchmark;
- cost, latency, and failure-mode reporting.

See [the roadmap](docs/ROADMAP.md) and
[experiment protocol](docs/EXPERIMENTS.md). Interpretation limits are recorded
in [threats to validity](docs/THREATS_TO_VALIDITY.md).

## 中文说明

这是一个研究 **AI Coding 可靠性** 的公开实验室。首个工具 Agent Scope
Guard 用来检查 Coding Agent 是否越过任务声明的文件边界。仓库只使用公开
或虚构案例，不包含任何公司内部代码、数据或业务规则。

## Contributing

Issues that include a minimal reproduction are welcome. Before proposing a
change, read [AGENTS.md](AGENTS.md) and run the local verification commands.
