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

Read [Experiment 001 ? Scope boundaries](experiments/001-scope-boundaries/README.md)
for the question, inputs, success criteria, result, and limitations.

## Repository map

```text
agent_scope_guard/   Scope policy engine and command-line interface
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

## ????

?????? **AI Coding ???** ??????????? Agent Scope
Guard ???? Coding Agent ?????????????????????
??????????????????????????

## Contributing

Issues that include a minimal reproduction are welcome. Before proposing a
change, read [AGENTS.md](AGENTS.md) and run the local verification commands.
