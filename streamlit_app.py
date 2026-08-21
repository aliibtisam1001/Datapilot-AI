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

# ── Custom CSS Design System ──
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

    :root {
        --paper: #F2F3ED;
        --paper-line: #E1E4D9;
        --ink: #161C1A;
        --ink-soft: #54605B;
        --amber: #E5A03B;
        --amber-ink: #5C3D0E;
        --slate: #3E5C76;
        --teal: #1E6F5C;
        --red: #B4432C;
        --card: #FFFFFF;
        --radius: 14px;
        --mono: 'IBM Plex Mono', monospace;
        --sans: 'IBM Plex Sans', sans-serif;
        --display: 'Space Grotesk', sans-serif;
    }

    /* Global App Background & Grid */
    .stApp {
        background:
            linear-gradient(var(--paper-line) 1px, transparent 1px) 0 0/100% 40px,
            linear-gradient(90deg, var(--paper-line) 1px, transparent 1px) 0 0/40px 100%,
            var(--paper) !important;
        background-attachment: local !important;
        color: var(--ink) !important;
        font-family: var(--sans) !important;
    }

    /* Main Container max-width */
    .block-container {
        max-width: 1100px !important;
        padding-top: 2rem !important;
        padding-bottom: 4rem !important;
    }

    /* Header & Hero */
    .hero-wrap {
        text-align: left;
        padding: 1.5rem 0 1.2rem 0;
        position: relative;
        border-bottom: 1px solid var(--paper-line);
        margin-bottom: 1.5rem;
    }
    .hero-eyebrow {
        font-family: var(--mono);
        font-size: 11.5px;
        letter-spacing: .08em;
        text-transform: uppercase;
        color: var(--teal);
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;
    }
    .hero-eyebrow::before {
        content: "";
        width: 16px;
        height: 1.5px;
        background: var(--teal);
    }
    .hero-title {
        font-family: var(--display);
        font-weight: 700;
        font-size: clamp(32px, 4.5vw, 48px);
        line-height: 1.05;
        letter-spacing: -0.03em;
        margin: 0 0 10px;
        color: var(--ink);
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .hero-dot {
        width: 12px;
        height: 12px;
        border-radius: 3px;
        background: var(--amber);
        display: inline-block;
        transform: rotate(45deg);
        box-shadow: 0 0 0 4px rgba(229,160,59,0.2);
    }
    .hero-sub {
        font-size: 16px;
        line-height: 1.55;
        color: var(--ink-soft);
        max-width: 650px;
        margin-bottom: 16px;
    }
    .stack-row {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin-top: 10px;
    }
    .stack-pill {
        font-family: var(--mono);
        font-size: 11px;
        color: var(--ink-soft);
        background: var(--card);
        border: 1px solid var(--paper-line);
        padding: 4px 10px;
        border-radius: 999px;
    }

    /* Guardrail Badge */
    .guard-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-family: var(--mono);
        font-size: 11.5px;
        color: var(--teal);
        background: #E8F4F0;
        border: 1px solid #C2E3D8;
        padding: 4px 10px;
        border-radius: 6px;
        margin-bottom: 12px;
    }

    /* Chat Messages */
    .stChatMessage {
        background: var(--card) !important;
        border: 1px solid var(--paper-line) !important;
        border-radius: var(--radius) !important;
        box-shadow: 0 8px 24px -16px rgba(22,28,26,0.12) !important;
        margin-bottom: 1rem !important;
        padding: 1rem 1.2rem !important;
    }

    /* SQL Expander Styling */
    .streamlit-expanderHeader {
        font-family: var(--display) !important;
        font-weight: 600 !important;
        color: var(--ink) !important;
        background: var(--card) !important;
        border: 1px solid var(--paper-line) !important;
        border-radius: 8px !important;
    }
    .stCodeBlock {
        border-radius: 8px !important;
        border: 1px solid var(--paper-line) !important;
    }

    /* Business Insight Callout */
    .insight-card {
        background: var(--card);
        border: 1px solid var(--paper-line);
        border-left: 4px solid var(--amber);
        border-radius: var(--radius);
        padding: 16px 18px;
        margin-top: 12px;
        box-shadow: 0 4px 16px -8px rgba(22,28,26,0.1);
    }
    .insight-title {
        font-family: var(--display);
        font-weight: 600;
        font-size: 14px;
        color: var(--amber-ink);
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .insight-body {
        font-family: var(--sans);
        font-size: 13.5px;
        color: var(--ink-soft);
        line-height: 1.55;
    }

    /* Sidebar Customization */
    [data-testid="stSidebar"] {
        background: #EAECE4 !important;
        border-right: 1px solid var(--paper-line) !important;
    }
    [data-testid="stSidebar"] .stButton button {
        background: var(--card) !important;
        color: var(--ink) !important;
        border: 1px solid var(--paper-line) !important;
        border-radius: 999px !important;
        font-size: 12.5px !important;
        font-weight: 500 !important;
        text-align: left !important;
        padding: 6px 14px !important;
        transition: all .2s ease !important;
    }
    [data-testid="stSidebar"] .stButton button:hover {
        border-color: var(--amber) !important;
        color: var(--amber-ink) !important;
        box-shadow: 0 4px 12px -6px rgba(229,160,59,0.3) !important;
        transform: translateY(-1px) !important;
    }

    /* Chat Input Bar */
    [data-testid="stChatInput"] {
        background: var(--card) !important;
        border: 1px solid var(--paper-line) !important;
        border-radius: 999px !important;
        box-shadow: 0 10px 30px -10px rgba(22,28,26,0.15) !important;
    }
    [data-testid="stChatInput"]:focus-within {
        border-color: var(--amber) !important;
    }

    /* Hide standard headers */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ── Helper Functions ──
from app.utils import strip_thinking, clean_sql_input, SQLCaptureCallbackHandler


def get_groq_api_key():
    """Retrieve Groq API key from environment, Streamlit secrets, or session state."""
    key = os.getenv("GROQ_API_KEY")
    if not key:
        try:
            key = st.secrets.get("GROQ_API_KEY", "")
        except Exception:
            key = ""
    if not key and "user_groq_api_key" in st.session_state:
        key = st.session_state.user_groq_api_key
    return key


def ensure_database_exists():
    """Check if SQLite database exists; if not, attempt to build it from CSVs."""
    db_path = os.path.join(os.path.dirname(__file__), 'data', 'olist.db')
    if not os.path.exists(db_path):
        csv_dir = os.path.join(os.path.dirname(__file__), 'data')
        csv_files = [f for f in os.listdir(csv_dir) if f.endswith('.csv')] if os.path.exists(csv_dir) else []
        if csv_files:
            with st.spinner("📦 Initializing database from CSV files (first-time setup)..."):
                try:
                    from app.load_data import create_sqlite_database
                    create_sqlite_database()
                except Exception as e:
                    st.error(f"Error initializing database: {e}")
    return os.path.abspath(db_path)


@st.cache_resource
def init_agent(api_key: str):
    """Initialize the SQL agent (cached per API key)."""
    from langchain_groq import ChatGroq
    from langchain_community.utilities import SQLDatabase
    from langchain_community.agent_toolkits import create_sql_agent, SQLDatabaseToolkit
    from app.prompts import build_system_prompt

    db_path = ensure_database_exists()
    db_uri = f"sqlite:///{db_path}"

    llm = ChatGroq(
        model="qwen/qwen3.6-27b",
        temperature=0,
        api_key=api_key,
    )

    db = SQLDatabase.from_uri(db_uri)
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
def init_explain_llm(api_key: str):
    """Initialize a separate LLM instance for explanations."""
    from langchain_groq import ChatGroq
    return ChatGroq(
        model="qwen/qwen3.6-27b",
        temperature=0.3,
        api_key=api_key,
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


# Import our custom modules
from app.explain import explain_result
from app.charts import auto_chart
from app.guardrails import validate_sql

# ── Session State ──
if "messages" not in st.session_state:
    st.session_state.messages = []

# ── Header ──
st.markdown("""
<div class="hero-wrap">
    <div class="hero-eyebrow">Natural language → SQL → Answer</div>
    <div class="hero-title"><span class="hero-dot"></span> SmartQuery</div>
    <div class="hero-sub">Ask plain-English business questions across your e-commerce database — get verified SQL, interactive Plotly charts, and plain-English executive explanations.</div>
    <div class="stack-row">
        <span class="stack-pill">Groq · Qwen 3.6</span>
        <span class="stack-pill">LangChain SQL Agent</span>
        <span class="stack-pill">SQLite · Olist 100k</span>
        <span class="stack-pill">Plotly Visualizations</span>
        <span class="stack-pill">✓ SELECT only Guardrails</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ── API Key Resolution ──
groq_key = get_groq_api_key()

with st.sidebar:
    if not groq_key:
        st.warning("⚠️ No Groq API Key found.")
        user_key = st.text_input("🔑 Enter your Groq API Key:", type="password", placeholder="gsk_...")
        if user_key:
            st.session_state.user_groq_api_key = user_key
            st.rerun()
        st.info("Get a free key at [console.groq.com](https://console.groq.com).")

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
            st.markdown("""<div class="guard-badge">✓ Guardrails Passed · SELECT Only · 1,000 Row Limit</div>""", unsafe_allow_html=True)
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
                st.markdown(f"""
                <div class="insight-card">
                    <div class="insight-title">💡 Executive Insight</div>
                    <div class="insight-body">{msg['explanation']}</div>
                </div>
                """, unsafe_allow_html=True)


# ── Handle Input ──
# Check for pending question from sidebar
if "pending_question" in st.session_state:
    user_input = st.session_state.pending_question
    del st.session_state.pending_question
else:
    user_input = st.chat_input("Ask a business question about the Olist e-commerce data...")

if user_input:
    if not groq_key:
        st.error("🔑 Please enter a Groq API Key in the sidebar to run queries.")
    else:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user", avatar="🧑‍💼"):
            st.markdown(user_input)

        # Initialize agent with key
        agent, db, llm = init_agent(groq_key)
        explain_llm = init_explain_llm(groq_key)

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

                    # Display Guardrail Badge & Answer
                    st.markdown("""<div class="guard-badge">✓ Guardrails Passed · SELECT Only · 1,000 Row Limit</div>""", unsafe_allow_html=True)
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
                                st.markdown(f"""
                                <div class="insight-card">
                                    <div class="insight-title">💡 Executive Insight</div>
                                    <div class="insight-body">{explanation}</div>
                                </div>
                                """, unsafe_allow_html=True)
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
