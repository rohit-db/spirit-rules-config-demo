# Using AI Dev Kit with This Project

AI Dev Kit gives your coding assistant (GitHub Copilot, Claude Code, Cursor) access to Databricks tools and context via MCP.

## Prerequisites

- VS Code with GitHub Copilot extension
- `uv` installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Databricks CLI with an authenticated profile (`databricks auth login <workspace-url>`)

## Install

```bash
bash <(curl -sL https://raw.githubusercontent.com/databricks-solutions/ai-dev-kit/main/install.sh)
```

This creates `~/.ai-dev-kit/` with the MCP server and writes `.vscode/mcp.json` in your project.

## Enable in VS Code

After install, you must manually enable the Databricks MCP server:

1. Open VS Code
2. Open the Command Palette (Cmd+Shift+P)
3. Search for "MCP: List Servers"
4. Find the `databricks` server and enable it

## Usage

Use Copilot in **Agent mode** (not standard chat) to access Databricks tools. Agent mode lets Copilot call MCP tools like querying tables, managing jobs, and interacting with your workspace.

Example prompts:
- "List the tables in the spirit_rules database"
- "Show me the last run of the setup_lakebase job"
- "What's the schema of the rule_headers table?"
- "Check the status of the Lakebase provisioned instance"
