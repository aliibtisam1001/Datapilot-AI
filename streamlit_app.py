"""
SmartQuery - Natural Language to SQL Business Intelligence Assistant.
Streamlit chat-style interface.
"""
import streamlit as st
import os
import re
import pandas as pd
import time
from dotenv import load_dotenv

load_dotenv()

# ── Page Config ──
st.set_page_config(
    page_title="SmartQuery — BI Assistant",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ──
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Global */
    .stApp {
        font-family: 'Inter', sans-serif;
    }

    /* Header */
    .main-header {
        text-align: center;
        padding: 1.5rem 0 1rem 0;
    }
    .main-header h1 {
        background: linear-gradient(135deg, #4FC3F7, #7C4DFF, #FF4081);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
    }
    .main-header p {
        color: #B0BEC5;
        font-size: 1.05rem;
        margin-top: 0.3rem;
    }

    /* Chat messages */
    .user-msg {
        background: linear-gradient(135deg, #1a237e, #283593);
        border-radius: 16px 16px 4px 16px;
        padding: 1rem 1.2rem;
        margin: 0.5rem 0;
        color: #e3f2fd;
        border-left: 3px solid #7C4DFF;
    }
    .bot-msg {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        border-radius: 16px 16px 16px 4px;
        padding: 1rem 1.2rem;
        margin: 0.5rem 0;
        color: #e0e0e0;
        border-left: 3px solid #4FC3F7;
    }

    /* SQL expander */
    .sql-block {
        background: #0d1117;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 1rem;
        font-family: 'Fira Code', 'Consolas', monospace;
        font-size: 0.85rem;
        color: #79c0ff;
        overflow-x: auto;
    }

    /* Metric display */
    .metric-card {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #4FC3F7;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #B0BEC5;
        margin-top: 0.3rem;
    }

    /* Input area styling */
    .stChatInput {
        border-color: #4FC3F7 !important;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ── Helper Functions ──
def strip_thinking(text: str) -> str:
    """Remove <think>...</think> blocks from model output."""
    if not text:
        return ""
    return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()


import ast
import json
from langchain_core.callbacks import BaseCallbackHandler

def clean_sql_input(raw):
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


@st.cache_resource
def init_agent():
    """Initialize the SQL agent (cached so it's only created once)."""
    from langchain_groq import ChatGroq
    from langchain_community.utilities import SQLDatabase
    from langchain_community.agent_toolkits import create_sql_agent, SQLDatabaseToolkit
    from app.prompts import build_system_prompt

    DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'olist.db')
    DB_URI = f"sqlite:///{os.path.abspath(DB_PATH)}"

    llm = ChatGroq(
        model="qwen/qwen3.6-27b",
        temperature=0,
        api_key=os.getenv("GROQ_API_KEY"),
    )

    db = SQLDatabase.from_uri(DB_URI)
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)

    agent = create_sql_agent(
        llm=llm,
        toolkit=toolkit,
        agent_type="tool-calling",
        prefix=build_system_prompt(),
        verbose=False,
        handle_parsing_errors=True,
        agent_executor_kwargs={"return_intermediate_steps": True},
    )

    return agent, db, llm


@st.cache_resource
def init_explain_llm():
    """Initialize a separate LLM instance for explanations."""
    from langchain_groq import ChatGroq
    return ChatGroq(
        model="qwen/qwen3.6-27b",
        temperature=0.3,
        api_key=os.getenv("GROQ_API_KEY"),
    )


def run_query_for_chart(db, sql):
    """Run a SQL query and return a DataFrame for charting."""
    if not sql:
        return pd.DataFrame()
    try:
        import sqlalchemy
        engine = sqlalchemy.create_engine(db._engine.url)
        with engine.connect() as conn:
            df = pd.read_sql(sql, conn)
        return df
    except Exception:
        return pd.DataFrame()


# ── Initialize ──
agent, db, llm = init_agent()
explain_llm = init_explain_llm()

# Import our custom modules
from app.explain import explain_result
from app.charts import auto_chart
from app.guardrails import validate_sql

# ── Session State ──
if "messages" not in st.session_state:
    st.session_state.messages = []

# ── Header ──
st.markdown("""
<div class="main-header">
    <h1>🔍 SmartQuery</h1>
    <p>Ask business questions in plain English — get SQL, charts, and insights instantly</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ──
with st.sidebar:
    st.markdown("### 💡 Example Questions")
    example_questions = [
        "What is the total revenue from delivered orders?",
        "Which 5 states have the most customers?",
        "How many orders were placed each month in 2018?",
        "What are the top 5 product categories by revenue?",
        "What is the average delivery time in days?",
        "What percentage of orders were canceled?",
        "Which payment type is most popular?",
        "What is the average review score?",
    ]
    for idx, q in enumerate(example_questions):
        if st.button(q, key=f"ex_{idx}", use_container_width=True):
            st.session_state.pending_question = q

    st.markdown("---")
    st.markdown("### ℹ️ About")
    st.markdown("""
    **SmartQuery** converts natural language questions into SQL, runs them against the **Olist Brazilian E-Commerce** database, and automatically generates interactive charts and business insights.
    
    **Tech Stack:**
    - **LLM:** Groq (`qwen3.6-27b`)
    - **Framework:** LangChain SQL Agent
    - **Database:** SQLite (100k+ orders)
    - **Visualization:** Plotly & Streamlit
    """)

    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ── Display Chat History ──
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user", avatar="🧑‍💼"):
            st.markdown(msg["content"])
    else:
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown(msg.get("answer", ""))

            # Show SQL in expander
            if msg.get("sql"):
                with st.expander("📝 Show SQL used", expanded=False):
                    st.code(msg["sql"], language="sql")

            # Show Data Table in expander
            if msg.get("df") is not None and not msg["df"].empty:
                with st.expander("📊 View Data Table", expanded=False):
                    st.dataframe(msg["df"], use_container_width=True)

            # Show chart
            if msg.get("chart"):
                st.plotly_chart(msg["chart"], use_container_width=True)

            # Show explanation
            if msg.get("explanation"):
                st.info(f"💡 **Business Insight:**\n\n{msg['explanation']}")


# ── Handle Input ──
# Check for pending question from sidebar
if "pending_question" in st.session_state:
    user_input = st.session_state.pending_question
    del st.session_state.pending_question
else:
    user_input = st.chat_input("Ask a business question about the Olist e-commerce data...")

if user_input:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="🧑‍💼"):
        st.markdown(user_input)

    # Process with agent
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("🔄 Querying the database..."):
            try:
                callback_handler = SQLCaptureCallbackHandler()
                result = agent.invoke(
                    {"input": user_input},
                    config={"callbacks": [callback_handler]}
                )
                answer = strip_thinking(result.get("output", "No answer generated."))

                # Extract SQL from callback or steps
                main_sql = None
                if callback_handler.sql_queries:
                    main_sql = callback_handler.sql_queries[-1]
                
                # If sql is found, sanitize & validate through guardrails
                df = pd.DataFrame()
                if main_sql:
                    try:
                        validated_sql = validate_sql(main_sql)
                        df = run_query_for_chart(db, validated_sql)
                    except Exception:
                        df = run_query_for_chart(db, main_sql)

                # Display answer
                st.markdown(answer)

                # Show SQL
                if main_sql:
                    with st.expander("📝 Show SQL used", expanded=False):
                        st.code(main_sql, language="sql")

                # Show Data Table
                if not df.empty:
                    with st.expander("📊 View Data Table", expanded=False):
                        st.dataframe(df, use_container_width=True)

                # Generate and show chart
                chart_fig = None
                if not df.empty:
                    try:
                        chart_fig = auto_chart(df, user_input)
                        if chart_fig:
                            st.plotly_chart(chart_fig, use_container_width=True)
                    except Exception as ce:
                        st.caption(f"Chart generation note: {ce}")

                # Generate and show explanation
                explanation = None
                if not df.empty:
                    try:
                        time.sleep(1)  # Buffer for rate limits
                        explanation = explain_result(
                            user_input, df, sql=main_sql, llm=explain_llm
                        )
                        if explanation:
                            st.info(f"💡 **Business Insight:**\n\n{explanation}")
                    except Exception:
                        pass  # Explanation is optional, don't break the flow

                # Save to history
                st.session_state.messages.append({
                    "role": "assistant",
                    "answer": answer,
                    "sql": main_sql,
                    "df": df,
                    "chart": chart_fig,
                    "explanation": explanation,
                })

            except Exception as e:
                error_msg = str(e)
                if "rate_limit" in error_msg.lower() or "429" in error_msg:
                    st.error("⏳ Rate limit reached. Please wait ~15 seconds and try again.")
                else:
                    st.error(f"❌ Error: {error_msg}")
                st.session_state.messages.append({
                    "role": "assistant",
                    "answer": f"Error: {error_msg}",
                    "sql": None,
                    "df": pd.DataFrame(),
                    "chart": None,
                    "explanation": None,
                })
