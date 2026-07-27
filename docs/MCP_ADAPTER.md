# MCP adapter

Agent Scope Guard includes a minimal, read-only Model Context Protocol (MCP)
stdio server. It lets a coding agent ask whether planned paths or a local Git
diff stay inside a reviewed scope policy.

The adapter targets the
[MCP 2025-11-25 lifecycle](https://modelcontextprotocol.io/specification/2025-11-25/basic/lifecycle),
[stdio transport](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports),
and [tools contract](https://modelcontextprotocol.io/specification/2025-11-25/server/tools).
It uses newline-delimited UTF-8 JSON-RPC and writes no logs to stdout.

## Install and configure

Install this package in the environment used by the MCP client:

```bash
python -m pip install git+https://github.com/altruylee/ai-coding-lab.git
```

Then add an stdio server to the client's MCP configuration:

```json
{
  "mcpServers": {
    "agent-scope-guard": {
      "command": "agent-scope-guard-mcp",
      "args": [
        "--repo-root",
        "/absolute/path/to/repository"
      ]
    }
  }
}
```

MCP client configuration locations and top-level keys differ. Treat
[`examples/mcp/server-config.json`](../examples/mcp/server-config.json) as the
server definition, then place it where the chosen client documents.

For a source checkout, the equivalent entry point is:

```bash
python -m agent_scope_guard.mcp_server \
  --repo-root /absolute/path/to/repository
```

The process working directory or `PYTHONPATH` must make the checked-out package
importable.

## Tools

### `scope_check_paths`

Checks an explicit list of repository-relative paths:

```json
{
  "policy": "examples/mcp/policy.json",
  "changed_paths": [
    "src/app.py",
    "tests/test_app.py"
  ]
}
```

### `scope_check_git_diff`

Uses local Git to list changed path names between two revisions, then applies
the policy:

```json
{
  "policy": "examples/mcp/policy.json",
  "base_ref": "main",
  "head_ref": "HEAD"
}
```

Both tools return `ok`, `changed_paths`, and `violations` as structured
content. A policy violation is a successful tool execution with `ok: false`;
invalid arguments, unsafe paths, unreadable policies, and Git failures return
an MCP tool execution error so an agent can correct its input.

## Safety boundary

The server:

- resolves policy files under the configured repository root;
- reads only the selected JSON policy;
- asks Git only for changed path names;
- passes Git arguments as an array without a shell and disables external diff
  and text-conversion drivers;
- rejects unsafe policy paths and malformed revision inputs;
- caps messages, changed-path counts, Git runtime, and calls per stdio session;
- performs no network requests and writes no files;
- exposes both tools as read-only, non-destructive, idempotent operations.

This is a scope signal, not an authorization system. A client or workflow must
still place human approval before mutations such as committing, pushing,
deploying, publishing, or changing external systems.

## Protocol scope and limitations

This standard-library implementation intentionally covers only initialization,
initialized notification handling, `ping`, `tools/list`, and `tools/call`.
It does not implement resources, prompts, sampling, tasks, Streamable HTTP,
authentication, or the complete official SDK surface, and it does not claim
full MCP conformance.

Other current limits:

- Git diff mode follows the existing `ACMR` path policy and excludes deletions.
- Rename source paths are not independently evaluated.
- The guard checks filenames and policy patterns, not source semantics.
- Symbolic links can affect what a policy filename resolves to; the final
  resolved path must still remain under the configured repository root.

## Verify

```bash
python scripts/verify_mcp_adapter.py
python -m unittest discover -s tests -p "test_mcp_server.py" -v
```
