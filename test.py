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


async def main():
    file_system_mcp = MCPClient()
    await file_system_mcp.connect_to_local_server("server.py")
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