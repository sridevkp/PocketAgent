import inspect, json, asyncio

class Tool:
    def __init__(self, func, name, description, schema):
        self.callable = func
        self.name = name or func.__name__
        self.description = description or inspect.getdoc(func) or "No description available"
        self.schema = schema

    def call(self, tool_input):
        if inspect.iscoroutinefunction(self.callable):
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                return asyncio.run(self.callable(**tool_input))
            else:
                return loop.run_until_complete(self.callable(**tool_input))
        else:
            return self.callable(**tool_input)

    async def acall(self, tool_input):
        if inspect.iscoroutinefunction(self.callable):
            return await self.callable(**tool_input)
        else:
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, lambda: self.callable(**tool_input))

    
    def __str__(self):
        if self.schema:
            schema_str = json.dumps(self.schema, indent=2)
        else:
            sig = str(inspect.signature(self.callable))
            schema_str = f"Parameters: {sig}"
        
        return f"""Tool: {self.name}
Description: {self.description}
Input Schema:
{schema_str}
"""