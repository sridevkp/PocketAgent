import json

from utils import extract_json_objects, tool_to_string
from system import SYSTEM_PROMPT_TEMPLATE
from llm import LLM


class Agent:
    def __init__(self, llm: LLM, context="You are a helpful assistant."):
        self.tools = {}
        self.llm = llm
        self.context = context

    def register_tool(self,func):
        def wrapper(*args,**kargs):
            print(f"running tool {func.__name__}")
            return func(*args,**kargs)

        self.tools[func.__name__] = func
        return wrapper

    def invoke(self, prompt, debug=False):
        tools = "\n".join(tool_to_string(func) for func in self.tools.values())

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
                            "observation": self.tools[tool_name](**tool_input)
                        }
                        if debug : print(f"[DEBUG:78] {observation}")
                        history.append({"role":"user", "content": json.dumps(observation)})
            except Exception as e:
                print(f"Something went wrong: {e}")
                break






