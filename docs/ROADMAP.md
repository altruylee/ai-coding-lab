# Roadmap

The lab develops small, measurable components rather than a monolithic agent
framework.

## Milestone 1 ? Scope

- [x] Declarative allowed, denied, and required path patterns
- [x] Explicit-path and Git-diff modes
- [x] Human-readable and JSON output
- [ ] Policy schema and editor integration
- [ ] Rename and deletion policies

## Milestone 2 ? Evidence

- [x] Record declared commands and observed exit status
- [x] Verify that declared checks ran successfully
- [x] Produce a machine-readable task evidence bundle
- [x] Hash evidence artifacts and their referenced inputs
- [ ] Sign evidence with CI-native identity

## Milestone 3 ? Reproducible tasks

- [ ] Define a compact coding-agent task format
- [x] Publish the first synthetic scope-boundary experiment
- [ ] Publish ten synthetic repository tasks
- [ ] Provide deterministic validation scripts
- [ ] Track success, cost, latency, and human intervention

## Milestone 4 ? Public benchmark

- [ ] Run at least two agent configurations on the same tasks
- [ ] Publish raw results and failure classifications
- [ ] Add community-submitted runs with provenance
- [ ] Document threats to validity

## Milestone 5 ? Integration

- [ ] GitHub Actions example
- [ ] Pre-commit integration
- [ ] MCP or agent-tool adapter
- [ ] Reference workflow with explicit human approval gates
