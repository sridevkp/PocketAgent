from agent import Agent
from tools import http_get
import random

agent = Agent()

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
