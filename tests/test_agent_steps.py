import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
from dotenv import load_dotenv

load_dotenv()

from langchain_groq import ChatGroq
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent, SQLDatabaseToolkit
from langchain_core.callbacks import BaseCallbackHandler

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'olist.db')
DB_URI = f"sqlite:///{os.path.abspath(DB_PATH)}"

llm = ChatGroq(
    model="qwen/qwen3.6-27b",
    temperature=0,
    api_key=os.getenv("GROQ_API_KEY"),
)

db = SQLDatabase.from_uri(DB_URI)
toolkit = SQLDatabaseToolkit(db=db, llm=llm)

class SQLCaptureHandler(BaseCallbackHandler):
    def __init__(self):
        self.sql_queries = []
        self.tool_calls = []

    def on_tool_start(self, serialized, input_str, **kwargs):
        tool_name = serialized.get('name') if isinstance(serialized, dict) else kwargs.get('name')
        print(f"DEBUG CALLBACK on_tool_start: {tool_name}, input: {input_str}")
        if tool_name in ('sql_db_query', 'sql_db_query_checker'):
            self.sql_queries.append(input_str)
        self.tool_calls.append({'tool': tool_name, 'input': input_str})

handler = SQLCaptureHandler()

agent = create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    agent_type="tool-calling",
    verbose=False,
    handle_parsing_errors=True,
    agent_executor_kwargs={"return_intermediate_steps": True},
)

res = agent.invoke({"input": "What are the top 5 product categories by revenue?"}, config={"callbacks": [handler]})

print("\n--- RESULTS ---")
print("Agent Output:", res.get("output"))
print("Captured Queries via Callback:", handler.sql_queries)
print("Res keys:", res.keys())
if "intermediate_steps" in res:
    print("Intermediate steps len:", len(res["intermediate_steps"]))
    print("Intermediate steps:", res["intermediate_steps"])
