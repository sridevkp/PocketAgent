import json

from .utils import extract_json_objects
from .system import SYSTEM_PROMPT_TEMPLATE
from .tool import Tool
from .llm import LLM



class Agent:
    def __init__(self, llm: LLM, context="You are a helpful assistant."):
        self.tools = {}
        self.mcp = {}
        self.llm = llm
        self.context = context

    def register_tool(self, func, description=None, schema=None):
        def wrapper(*args,**kargs):
            print(f"Running tool {func.__name__}")
            return func(*args,**kargs)

        self.tools[func.__name__] = Tool(
            wrapper,
            name=func.__name__,
            description=description or func.__doc__ or "No description available",
            schema=schema
        )
        return wrapper
    
    def register_mcp(self,mcp_client):
        self.mcp = mcp_client

        for tool in mcp_client.tools:
            name = tool.name

            async def mcp_tool_wrapper(**kwargs):
                print(f"Calling MCP tool {name} with {kwargs}")
                response = await mcp_client.session.call_tool(name, kwargs)
                return response.content[0].text if response.content else None

            self.tools[name] = Tool(
                mcp_tool_wrapper,
                name=name,
                description=tool.description,
                schema=tool.inputSchema
            )


    async def ainvoke(self, prompt, debug=False):
        tools = "\n".join( str(tool) for tool in self.tools.values())
        SYSTEM_PROMPT = SYSTEM_PROMPT_TEMPLATE.format(context=self.context,tools=tools)

        history = [
            {"role": "user", "content": json.dumps({"type": "user", "user": prompt})}
        ]

        while True:
            try:
                response = self.llm.generate_response(system_instruction=SYSTEM_PROMPT, content=history)
                if debug : print(f"[DEBUG:57] {repr(response)}")

                steps = extract_json_objects(response)
                for step in steps:
                    history.append({"role": "user", "content": json.dumps(step)})
                    
                    if step.get("type") == "output":
                        return step.get("output")
                    
                    if step.get("type") == "action":
                        tool_name = step.get("function")
                        tool_input = step.get("input")

                        if tool_name not in self.tools:
                            print(f"Unknown tool: {tool_name}")
                            break

                        observation = {
                            "type": "observation",
                            "observation": await self.tools[tool_name].acall(tool_input)
                        }
                        if debug : print(f"[DEBUG:78] {observation}")
                        history.append({"role":"user", "content": json.dumps(observation)})
            except Exception as e:
                print(f"Something went wrong: {e}")
                break


