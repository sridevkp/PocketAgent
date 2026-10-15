import json
import random, os
import asyncio
from dotenv import load_dotenv
load_dotenv()

from pocket_agent.llm import MistralLLM, GenaiLLM, CoherelLLM
from pocket_agent.agent import Agent
from tools import http_get
from pocket_agent.mcp_client import MCPClient


# llm = GenaiLLM(os.getenv("GEMINI_API_KEY"))
# llm = MistralLLM(os.getenv("MISTRAL_API_KEY"))
MCP_SMOKE_TEST = os.getenv("MCP_SMOKE_TEST", "").lower() in {"1", "true", "yes"}

if MCP_SMOKE_TEST:
    llm = None
else:
    llm = CoherelLLM(api_key=os.getenv("COHERE_API_KEY"))

agent = Agent(llm=llm)

@agent.register_tool
def calculator(expression: str) -> int:
    """
    Evaluate a math expression and return the result.
    """
    return eval(expression)


@agent.register_tool
def get_temperature(place_name: str) -> int:
    """
    Returns atmosphere temperature in place.
    """
    return random.randrange(23,40)

agent.register_tool(http_get)


async def connect_mcp(client: MCPClient):
    transport = os.getenv("MCP_TRANSPORT", "local").lower()
    if transport == "sse":
        server_url = os.getenv("MCP_SSE_URL")
        if not server_url:
            raise ValueError("MCP_SSE_URL is required when MCP_TRANSPORT=sse")
        headers = json.loads(os.getenv("MCP_SSE_HEADERS", "{}"))
        await client.connect_to_sse_server(server_url, headers=headers)
    else:
        await client.connect_to_local_server("fs-server.py")


async def run_mcp_smoke_test():
    file_system_mcp = MCPClient()
    try:
        await connect_mcp(file_system_mcp)
        agent.register_mcp(file_system_mcp)

        if not file_system_mcp.tools:
            raise RuntimeError("No MCP tools were discovered from the server.")

        missing_tools = [tool.name for tool in file_system_mcp.tools if tool.name not in agent.tools]
        if missing_tools:
            raise RuntimeError(f"MCP tools not registered on agent: {missing_tools}")

        tool_name = os.getenv("MCP_SMOKE_TOOL", file_system_mcp.tools[0].name)
        tool_input = json.loads(os.getenv("MCP_SMOKE_INPUT", "{}"))
        result = await agent.tools[tool_name].acall(tool_input)
        print(f"[SMOKE] MCP tool '{tool_name}' call succeeded: {result}")
    finally:
        await file_system_mcp.close()
        print("🔌 MCP connection closed.")


async def main():
    if MCP_SMOKE_TEST:
        await run_mcp_smoke_test()
        return

    file_system_mcp = MCPClient()
    await connect_mcp(file_system_mcp)
    agent.register_mcp(file_system_mcp)

    try:
        while True:
            prompt = input("> ").strip()
            if prompt:
                if prompt in ["thanks", "exit", "tq"]:
                    break
                output = await agent.ainvoke(prompt, True)
                print(f"@ {output}")
    finally:
        await file_system_mcp.close()
        print("🔌 MCP connection closed.")


if __name__ == "__main__":
    asyncio.run(main())