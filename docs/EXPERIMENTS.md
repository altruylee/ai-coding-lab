# Experiment protocol

Every experiment in this repository should be independently reproducible.

## Required fields

An experiment report must identify:

1. the question being tested;
2. the public or synthetic repository state;
3. the task given to the coding agent;
4. the model and agent configuration;
5. tools and permissions available to the agent;
6. deterministic validation commands;
7. success criteria;
8. elapsed time and, when available, cost or token usage;
9. human interventions;
10. failures, limitations, and unexpected behavior.

## Evidence

Check in the smallest useful evidence bundle:

- task definition;
- policy;
- final patch;
- validation output;
- structured result summary.

Do not publish hidden reasoning, credentials, private prompts, private source
code, customer data, or employer-owned material.

## Comparison rules

- Run compared configurations against the same starting commit.
- Keep permissions and validation rules equal unless they are the variable.
- Repeat unstable runs and publish the variance.
- Treat a partial result as partial; do not convert it into a binary success.
- Separate observed results from interpretation.
- Do not treat fixtures, human solutions, or reference-exposed runs as agent
  leaderboard entries.
- Preserve unavailable token or cost metrics as `null`; never estimate them.
