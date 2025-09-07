from agent import Agent
from llm import MistralLLM, GenaiLLM, CoherelLLM
from tools import http_get
import random, os
from dotenv import load_dotenv
load_dotenv()


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


while True:
    prompt = input("> ").strip()
    if prompt:
        if prompt in ["thanks", "exit", "tq"]:
            break
        output = agent.invoke(prompt, True)
        print(f"@ {output}")
