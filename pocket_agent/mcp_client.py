import sys
import httpx2
from contextlib import AsyncExitStack

from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.streamable_http import streamable_http_client
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

        command = sys.executable if is_python else "node"
        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            env=None,
        )

        try:
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            self.stdio, self.write = stdio_transport

            await self._initialize_session()
        except BaseException:
            await self.exit_stack.aclose()
            raise

    async def connect_to_streamable_http_server(
        self,
        server_url: str,
        bearer_token: str | None = None,
        headers: dict[str, str] | None = None,
    ):
        """
        Connect to a remote MCP server over Streamable HTTP.

        bearer_token: An already-issued access token, if required.
        headers: Optional additional HTTP headers.
        """
        try:
            request_headers = dict(headers or {})

            if bearer_token:
                request_headers["Authorization"] = (
                    f"Bearer {bearer_token}"
                )

            # HTTP configuration, including headers, belongs here.
            http_client = await self.exit_stack.enter_async_context(
                httpx2.AsyncClient(
                    headers=request_headers,
                    timeout=httpx2.Timeout(
                        300.0,
                        connect=30.0,
                        write=30.0,
                        pool=30.0,
                    ),
                )
            )

            # Streamable HTTP returns read, write and session ID getter.
            read_stream, write_stream, _ = (
                await self.exit_stack.enter_async_context(
                    streamable_http_client(
                        server_url,
                        http_client=http_client,
                    )
                )
            )

            self.stdio = read_stream
            self.write = write_stream

            await self._initialize_session()

        except BaseException:
            await self.exit_stack.aclose()
            raise

    async def _initialize_session(self):
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
