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

## Repository map

```text
agent_scope_guard/   Scope policy engine and command-line interface
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
[experiment protocol](docs/EXPERIMENTS.md).

## 中文说明

这是一个研究 **AI Coding 可靠性** 的公开实验室。首个工具 Agent Scope
Guard 用来检查 Coding Agent 是否越过任务声明的文件边界。仓库只使用公开
或虚构案例，不包含任何公司内部代码、数据或业务规则。

## Contributing

Issues that include a minimal reproduction are welcome. Before proposing a
change, read [AGENTS.md](AGENTS.md) and run the local verification commands.
