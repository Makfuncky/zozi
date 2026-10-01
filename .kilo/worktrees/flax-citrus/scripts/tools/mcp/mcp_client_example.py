"""
MCP Client Example
==================
Demonstrates how any LLM (or application) can call Zozi AI Providers via MCP.

Usage:
    1. Start the MCP server:
       python mcp_server.py

    2. In another terminal, run this example:
       python mcp_client_example.py

    3. Or integrate with any MCP client:
       from mcp import ClientSession, StdioServerParameters
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_stdio():
    """Test the MCP server via stdio transport.

    Sends a list_tools request and prints the available tools.
    """
    import subprocess

    proc = subprocess.Popen(
        [sys.executable, "mcp_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=os.path.dirname(os.path.abspath(__file__)),
    )

    # Send JSON-RPC request to list tools
    request = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {},
    })
    stdout, stderr = proc.communicate(input=request, timeout=10)

    if stderr:
        print("Server stderr:", stderr[:500])

    try:
        response = json.loads(stdout)
        tools = response.get("result", {}).get("tools", [])
        print(f"\n{'='*60}")
        print(f"  Zozi AI Providers MCP — {len(tools)} tools available")
        print(f"{'='*60}")
        for tool in tools:
            print(f"\n  📌 {tool['name']}")
            print(f"     {tool.get('description', '')[:120]}")
    except json.JSONDecodeError:
        print("Raw output:", stdout[:1000])

    proc.terminate()


def test_httpx():
    """Test the MCP server via SSE HTTP transport.

    Requires the server to be started with SSE transport:
        python mcp_server.py --transport sse --port 8001
    """
    try:
        import httpx
    except ImportError:
        print("httpx not installed. Skipping HTTP test.")
        print("Install: pip install httpx")
        return

    print("\nTo test via HTTP, run:")
    print("  python mcp_server.py --transport sse --port 8001")
    print("Then in another terminal:")
    print("  python -c \"from mcp_client_example import test_httpx; test_httpx()\"")
    print("(Requires httpx: pip install httpx)")


if __name__ == "__main__":
    test_stdio()
