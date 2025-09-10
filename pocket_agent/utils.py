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


def _strip_code_fences(s: str) -> str:
    s = re.sub(r'```(?:json)?\s*', '', s, flags=re.IGNORECASE)
    s = s.replace('```', '')
    return s.strip()

def find_next_start(s: str, idx: int) -> int:
    p1 = s.find('{', idx)
    p2 = s.find('[', idx)
    if p1 == -1: return p2
    if p2 == -1: return p1
    return min(p1, p2)

def extract_json_objects(text: str) :
    text = _strip_code_fences(text)
    decoder = json.JSONDecoder()
    pos = 0
    end = len(text)
    objs = []

    while True:
        pos = find_next_start(text, pos)
        if pos == -1:
            break

        try:
            obj, next_pos = decoder.raw_decode(text, pos)
            objs.append(obj)
            pos = next_pos 
        except ValueError:
            pos += 1
            if pos >= end:
                break

    return objs

