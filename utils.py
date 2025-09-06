import inspect, re, json

def tool_to_string(func):
    sig = str(inspect.signature(func))        
    doc = inspect.getdoc(func) or "No description"
    return f"- {func.__name__}{sig}: {doc}"


def clean_json_response(msg: str):
    try:
        return json.loads(msg)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', msg, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        else:
            raise ValueError(f"No JSON found in message: {msg}")
