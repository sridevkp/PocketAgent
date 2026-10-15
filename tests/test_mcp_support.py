import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from pocket_agent.agent import Agent
from pocket_agent.mcp_client import MCPClient


class TestMCPSupport(unittest.IsolatedAsyncioTestCase):
    async def test_connect_to_sse_server_initializes_session(self):
        mcp_client = MCPClient()
        fake_session = SimpleNamespace(
            initialize=AsyncMock(),
            list_tools=AsyncMock(return_value=SimpleNamespace(tools=[SimpleNamespace(name="search")])),
        )
        mcp_client.exit_stack.enter_async_context = AsyncMock(
            side_effect=[("read_stream", "write_stream"), fake_session]
        )

        with patch("pocket_agent.mcp_client.sse_client") as mock_sse_client, patch(
            "pocket_agent.mcp_client.ClientSession", return_value="session_cm"
        ) as mock_session_ctor:
            await mcp_client.connect_to_sse_server(
                "http://localhost:3000/sse", headers={"Authorization": "******"}
            )

        mock_sse_client.assert_called_once_with(
            "http://localhost:3000/sse", headers={"Authorization": "******"}
        )
        mock_session_ctor.assert_called_once_with("read_stream", "write_stream")
        fake_session.initialize.assert_awaited_once()
        fake_session.list_tools.assert_awaited_once()
        self.assertEqual([tool.name for tool in mcp_client.tools], ["search"])

    async def test_register_mcp_binds_each_tool_name(self):
        async def _call_tool(name, _kwargs):
            return SimpleNamespace(content=[SimpleNamespace(text=name)])

        fake_session = SimpleNamespace(call_tool=AsyncMock(side_effect=_call_tool))
        fake_mcp_client = SimpleNamespace(
            tools=[
                SimpleNamespace(name="tool_a", description="A", inputSchema={}),
                SimpleNamespace(name="tool_b", description="B", inputSchema={}),
            ],
            session=fake_session,
        )

        agent = Agent(llm=None)
        agent.register_mcp(fake_mcp_client)

        result_a = await agent.tools["tool_a"].acall({})
        result_b = await agent.tools["tool_b"].acall({})

        self.assertEqual(result_a, "tool_a")
        self.assertEqual(result_b, "tool_b")
        self.assertEqual(
            [call.args[0] for call in fake_session.call_tool.await_args_list],
            ["tool_a", "tool_b"],
        )


if __name__ == "__main__":
    unittest.main()
