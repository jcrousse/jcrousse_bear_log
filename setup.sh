#!/usr/bin/env bash
set -euo pipefail

echo "=== Bear Log MCP Server Setup ==="

# Check for uv
if ! command -v uv &>/dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

echo "uv found: $(uv --version)"

# Check for git
if ! command -v git &>/dev/null; then
    echo "ERROR: git is required but not installed."
    exit 1
fi

# Verify we're in the repo
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ ! -f "$SCRIPT_DIR/mcp_server.py" ]; then
    echo "ERROR: mcp_server.py not found. Run this script from the repo root."
    exit 1
fi

# Pre-fetch dependencies and verify the server starts
echo "Installing dependencies and verifying server..."
cd "$SCRIPT_DIR"
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
    | timeout 30 uv run mcp_server.py 2>/dev/null | python3 -c "
import sys, json
resp = json.loads(sys.stdin.readline())
name = resp['result']['serverInfo']['name']
print(f'Server \"{name}\" responds OK')
"

echo ""
echo "Setup complete! Start the server with:"
echo "  uv run $SCRIPT_DIR/mcp_server.py"
