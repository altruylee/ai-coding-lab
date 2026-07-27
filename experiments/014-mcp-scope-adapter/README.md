# Experiment 014: MCP scope adapter

## Question

Can Agent Scope Guard expose its existing path policy as a safe, interoperable
tool for MCP-capable coding agents without adding runtime dependencies or
granting mutation authority?

## Design

The experiment adds a minimal stdio MCP server with two tools:

1. evaluate an explicit list of repository-relative changed paths;
2. list names from a local Git comparison and evaluate those paths.

A deterministic verifier creates a synthetic Git repository and checks
initialization, tool discovery, an allowed explicit scope, a denied synthetic
key filename, an allowed Git diff, and a policy path traversal attempt.

The fixture contains no real key value, network request, private repository, or
employer data.

## Success criteria

1. The server completes MCP initialization and lists exactly two read-only tools.
2. Allowed explicit paths and an allowed Git diff return `ok: true`.
3. A denied synthetic path returns `ok: false` as a valid tool result.
4. A policy path escaping the repository returns a tool execution error.
5. Stdout contains only one-line JSON-RPC messages.
6. The full repository tests and supported Python CI jobs remain green.

## Result

All deterministic scenarios pass. The evidence bundle records normalized
output hashes for the end-to-end verifier, syntax compilation, and Experiment
013 compatibility.

## Reproduce

```bash
python scripts/verify_mcp_adapter.py
python -m unittest discover -s tests -p "test_mcp_server.py" -v
python -m agent_scope_guard evidence \
  --manifest experiments/014-mcp-scope-adapter/manifest.json \
  --output experiments/014-mcp-scope-adapter/evidence.json \
  --repo-root . \
  --verify
```

## Limitations

- This is a focused MCP tools adapter, not a complete SDK implementation or
  full protocol-conformance claim.
- The adapter informs an agent about scope; it cannot force an MCP client to
  request approval before writing.
- Git mode checks added, copied, modified, and renamed destination paths, but
  not deletion or rename source paths.
- Filename scope is not a substitute for semantic review, tests, or sandboxing.
