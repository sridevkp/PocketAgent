from google.genai.types import Content, GenerateContentConfig, Part
from google import genai
import json

from utils import clean_json_response, tool_to_string
from system import SYSTEM_PROMPT_TEMPLATE


API_KEY = "AIzaSyBjBVN-yPEkuBCumrpCX9c3AVVgRdbSzds"

client = genai.Client(api_key=API_KEY)




class Agent:
    def __init__(self):
        self.tools = {}
    
    def llm(self, system_instruction, history):
        contents = [
            Content(
                role=entry["role"],
                parts=[Part(text=entry["content"])]
            )
            for entry in history
        ]
        print(contents)

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=GenerateContentConfig(system_instruction=system_instruction)
        )

        return response.candidates[0].content.parts[0].text

    def register_tool(self,func):
        def wrapper(*args,**kargs):
            print(f"running tool {func.__name__}")
            return func(*args,**kargs)

        self.tools[func.__name__] = func
        return wrapper

    def invoke(self, prompt, debug=False):
        tools = "\n".join(tool_to_string(func) for func in self.tools.values())

        SYSTEM_PROMPT = SYSTEM_PROMPT_TEMPLATE.format(tools=tools)

        history = [
            {"role": "user", "content": json.dumps({"type": "user", "user": prompt})}
        ]

        while True:
            msg = self.llm(SYSTEM_PROMPT, history)
            if debug : print(f"[DEBUG:62] {repr(msg)}")
            try:
                response = clean_json_response(msg)
                history.append({"role": "model", "content": msg})

                if response.get("type") == "output":
                    return response.get("output")
                
                if response.get("type") == "action":
                    tool_name = response.get("function")
                    tool_input = response.get("input")

                    if tool_name not in self.tools:
                        print(f"Unknown tool: {tool_name}")
                        break

                    observation = {
                        "type": "observation",
                        "observation": self.tools[tool_name](**tool_input)
                    }
                    if debug : print(f"[DEBUG:82] {observation}")
                    history.append({"role":"user", "content": json.dumps(observation)})

            except Exception as e:
                print(f"Something went wrong: {e}")
                break














    #           action 
    #         7         \
    #        /           \
    #       /             \|
    #   thought <------- observation ------> output