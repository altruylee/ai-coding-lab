# Roadmap

The lab develops small, measurable components rather than a monolithic agent
framework.

## Milestone 1 — Scope

- [x] Declarative allowed, denied, and required path patterns
- [x] Explicit-path and Git-diff modes
- [x] Human-readable and JSON output
- [ ] Policy schema and editor integration
- [ ] Rename and deletion policies

## Milestone 2 — Evidence

- [x] Record declared commands and observed exit status
- [x] Verify that declared checks ran successfully
- [x] Produce a machine-readable task evidence bundle
- [x] Hash evidence artifacts and their referenced inputs
- [ ] Sign evidence with CI-native identity

## Milestone 3 — Reproducible tasks

- [x] Define a compact coding-agent task format
- [x] Publish the first synthetic scope-boundary experiment
- [x] Validate a failing starter and passing reference task
- [x] Publish ten synthetic repository tasks (10/10)
- [x] Provide deterministic validation scripts
- [x] Define success, cost, latency, and human-intervention fields
- [x] Publish the first blinded agent attempt with recorded metrics

## Milestone 4 — Public benchmark

- [x] Run at least two agent configurations on the same task
- [ ] Publish raw results and failure classifications
- [x] Define provenance rules for recorded and community-submitted runs
- [ ] Accept the first independently reproduced community run
- [ ] Document threats to validity

## Milestone 5 — Integration

- [ ] GitHub Actions example
- [ ] Pre-commit integration
- [ ] MCP or agent-tool adapter
- [ ] Reference workflow with explicit human approval gates
