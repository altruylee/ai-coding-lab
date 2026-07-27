# Threats to validity

The lab reports observed outcomes, not universal model capability. Interpret
every result within the following constraints.

## Task and test validity

- Synthetic tasks may not represent the complexity of production repositories.
- Public tests can reward code tailored to visible examples.
- A passing reference proves the declared tests are solvable, not that the
  tests cover every requirement.
- A mismatch between prose and tests can make prompt-context comparisons measure
  contract disclosure rather than general coding ability.

Experiment 011 found exactly this issue in Task 009: the specification-only
prompt said invalid values were rejected but did not state one exception class
for every invalid type. Public tests required `ValueError`, while two isolated
agents independently chose `TypeError` for type mismatches.

## Run independence

- Repeated attempts use fresh contexts, but they share the same task,
  orchestrator, agent family, and evaluation code.
- Small samples are not stable success-rate estimates.
- Parallel scheduling can affect wall-clock latency.
- Provider token and cost data may be unavailable.

## Model disclosure

Recorded attempts identify the GPT-5 family because the exact deployment is not
exposed. Results cannot distinguish silent provider updates or exact model
variants.

## Selection and comparison

- Tasks are selected by the maintainers, so selection bias is possible.
- Different tasks are not independent repetitions of the same difficulty.
- Multiple prompt comparisons increase the chance of an interesting result by
  coincidence.
- Failed and protocol-deviation runs must remain visible to reduce survivorship
  bias.

## Execution boundary

The runner isolates candidate overlays in temporary workspaces and validates
declared paths. It is not an operating-system security sandbox. Untrusted
community code should run in a restricted container or equivalent environment.

## Appropriate claims

The evidence supports statements such as “configuration A passed 4 of 6
recorded attempts.” It does not support “configuration A is 67% reliable” or
“configuration B is better” without substantially more preregistered,
independent repetitions.
