import asyncio
from contextlib import AsyncExitStack
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession


class MCPClient:
    def __init__(self):
        self.exit_stack = AsyncExitStack()
        self.stdio = None
        self.write = None
        self.session = None
        self.tools = []

    async def connect_to_local_server(self, server_script_path: str):
        """Connect to an MCP server (.py or .js)"""
        is_python = server_script_path.endswith(".py")
        is_js = server_script_path.endswith(".js")

        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")

        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            env=None,
        )

        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        self.stdio, self.write = stdio_transport

        self.session = await self.exit_stack.enter_async_context(
            ClientSession(self.stdio, self.write)
        )

        await self.session.initialize()

        # List available tools
        response = await self.session.list_tools()
        self.tools = response.tools
        print("[DEBUG] Connected to server with tools:", [t.name for t in self.tools])

    async def close(self):
        """Gracefully close all resources"""
        await self.exit_stack.aclose()
