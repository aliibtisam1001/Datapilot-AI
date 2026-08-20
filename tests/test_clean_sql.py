import ast
import json
import re

def clean_sql_input(raw):
    if isinstance(raw, dict):
        return raw.get('query', raw.get('sql', ''))
    if not isinstance(raw, str):
        return str(raw)
    raw = raw.strip()
    # Try ast literal eval for Python dict strings like "{'query': 'SELECT...'}"
    if raw.startswith('{') and raw.endswith('}'):
        try:
            parsed = ast.literal_eval(raw)
            if isinstance(parsed, dict):
                return parsed.get('query', parsed.get('sql', raw))
        except Exception:
            pass
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed.get('query', parsed.get('sql', raw))
        except Exception:
            pass
    # If wrapped in SQL quotes or regex
    m = re.search(r"['\"]query['\"]\s*:\s*['\"](.*?)['\"](?:\s*\}|$)", raw, re.DOTALL)
    if m:
        return m.group(1).encode().decode('unicode-escape')
    return raw

# Test inputs
cases = [
    "{'query': 'SELECT count(*) FROM orders;'}",
    '{"query": "SELECT count(*) FROM orders;"}',
    "SELECT count(*) FROM orders;",
    {'query': 'SELECT count(*) FROM orders;'}
]

for c in cases:
    print("IN:", repr(c))
    print("OUT:", repr(clean_sql_input(c)))
