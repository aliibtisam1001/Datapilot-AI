"""
SmartQuery Utility Functions.
Provides text cleaning, SQL extraction, and callback handlers for SQL capture.
"""
import ast
import json
import re
from langchain_core.callbacks import BaseCallbackHandler


def strip_thinking(text: str) -> str:
    """Remove <think>...</think> blocks from model output."""
    if not text:
        return ""
    return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()


def clean_sql_input(raw) -> str:
    """Extract clean SQL string from tool inputs that might be strings, dicts, or JSON/Python literals."""
    if isinstance(raw, dict):
        return raw.get('query', raw.get('sql', ''))
    if not isinstance(raw, str):
        return str(raw)
    raw = raw.strip()
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
    return raw


class SQLCaptureCallbackHandler(BaseCallbackHandler):
    """Callback to reliably capture SQL queries executed by the agent."""
    def __init__(self):
        self.sql_queries = []

    def on_tool_start(self, serialized, input_str, **kwargs):
        tool_name = serialized.get('name') if isinstance(serialized, dict) else kwargs.get('name')
        if tool_name == 'sql_db_query':
            cleaned = clean_sql_input(input_str)
            if cleaned and cleaned.upper().strip().startswith(('SELECT', 'WITH')):
                self.sql_queries.append(cleaned)
