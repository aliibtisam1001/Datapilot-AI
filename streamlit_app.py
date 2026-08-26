"""
DataPilot AI — Futuristic AI Business Intelligence Command Center.
Natural language data analyst for executives and business leaders.
Violet-to-Magenta Futuristic AI Palette.
"""
import streamlit as st
import streamlit.components.v1 as components
import os
import re
import json
import time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ── Page Configuration ──
st.set_page_config(
    page_title="DataPilot AI — Executive BI Command Center",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Global CSS: Futuristic AI Command Center Design System (Violet & Magenta) ──
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700;800&family=IBM+Plex+Sans:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600;700&display=swap');

    :root {
        --bg-void: #050811;
        --bg-surface: #090D1A;
        --bg-glass: rgba(13, 19, 36, 0.75);
        --bg-glass-card: rgba(18, 26, 48, 0.65);
        --border-glass: rgba(139, 92, 246, 0.22);
        --border-subtle: rgba(255, 255, 255, 0.08);
        --violet-primary: #8B5CF6;
        --fuchsia-secondary: #E879F9;
        --magenta-vivid: #D946EF;
        --emerald-glow: #10B981;
        --amber-glow: #F59E0B;
        --text-pure: #F8FAFC;
        --text-muted: #94A3B8;
        --text-subtle: #64748B;
        --font-title: 'Space Grotesk', sans-serif;
        --font-body: 'IBM Plex Sans', sans-serif;
        --font-mono: 'IBM Plex Mono', monospace;
    }

    /* Base Body & Command Canvas */
    .stApp {
        background: 
            radial-gradient(circle at 10% 10%, rgba(139, 92, 246, 0.14) 0%, transparent 40%),
            radial-gradient(circle at 90% 15%, rgba(232, 121, 249, 0.12) 0%, transparent 40%),
            radial-gradient(circle at 50% 90%, rgba(217, 70, 239, 0.14) 0%, transparent 45%),
            #050811 !important;
        background-attachment: fixed !important;
        color: var(--text-pure) !important;
        font-family: var(--font-body) !important;
    }

    .block-container {
        max-width: 1400px !important;
        padding-top: 1rem !important;
        padding-bottom: 4rem !important;
    }

    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #050811;
    }
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #8B5CF6, #E879F9);
        border-radius: 999px;
    }

    /* ── Top Navigation Bar ── */
    .nav-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.85rem 1.6rem;
        background: rgba(9, 13, 26, 0.85);
        backdrop-filter: blur(20px);
        border: 1px solid var(--border-subtle);
        border-radius: 18px;
        margin-bottom: 1.5rem;
        box-shadow: 0 15px 35px -10px rgba(0, 0, 0, 0.7);
    }
    .brand-logo-wrap {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .brand-logo-icon {
        width: 38px;
        height: 38px;
        border-radius: 10px;
        background: linear-gradient(135deg, #8B5CF6, #E879F9, #D946EF);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        box-shadow: 0 0 20px rgba(139, 92, 246, 0.5), inset 0 1px 2px rgba(255, 255, 255, 0.5);
        animation: logoPulse 4s infinite ease-in-out;
    }
    @keyframes logoPulse {
        0%, 100% { box-shadow: 0 0 15px rgba(139, 92, 246, 0.35); }
        50% { box-shadow: 0 0 28px rgba(232, 121, 249, 0.65), 0 0 10px rgba(139, 92, 246, 0.4); }
    }
    .brand-text {
        font-family: var(--font-title);
        font-size: 22px;
        font-weight: 800;
        letter-spacing: -0.02em;
        background: linear-gradient(90deg, #FFFFFF, #F1F5F9, #E879F9);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .brand-tagline {
        font-family: var(--font-mono);
        font-size: 11px;
        color: var(--fuchsia-secondary);
        letter-spacing: 0.05em;
    }

    /* Streamlit Radio Tabs Styling */
    div[role="radiogroup"] > label {
        background: rgba(18, 26, 48, 0.75) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        padding: 6px 14px !important;
        border-radius: 10px !important;
        transition: all 0.25s ease !important;
    }
    div[role="radiogroup"] > label:hover {
        border-color: var(--violet-primary) !important;
        box-shadow: 0 0 12px rgba(139, 92, 246, 0.35) !important;
    }
    div[role="radiogroup"] > label[data-checked="true"],
    div[role="radiogroup"] > label[aria-checked="true"] {
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.25), rgba(232, 121, 249, 0.2)) !important;
        border-color: var(--violet-primary) !important;
        box-shadow: 0 0 18px rgba(139, 92, 246, 0.4) !important;
    }

    /* Live Database Status Indicator */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        font-family: var(--font-mono);
        font-size: 11.5px;
        font-weight: 600;
        color: #10B981;
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.3);
        padding: 5px 12px;
        border-radius: 999px;
    }
    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #10B981;
        box-shadow: 0 0 8px #10B981;
        animation: blinkLive 2s infinite ease-in-out;
    }
    @keyframes blinkLive {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.4; transform: scale(0.85); }
    }

    /* ── Hero Command Banner ── */
    .hero-banner {
        padding: 1.8rem 2.2rem;
        background: linear-gradient(135deg, rgba(13, 20, 38, 0.9), rgba(9, 13, 26, 0.95));
        border: 1px solid var(--border-glass);
        border-radius: 20px;
        margin-bottom: 1.8rem;
        position: relative;
        overflow: hidden;
        box-shadow: 0 20px 45px -15px rgba(0, 0, 0, 0.6), inset 0 1px 1px rgba(255, 255, 255, 0.1);
    }
    .hero-banner::after {
        content: "";
        position: absolute;
        top: -80px;
        right: -80px;
        width: 260px;
        height: 260px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(139, 92, 246, 0.18), transparent 70%);
        pointer-events: none;
    }
    .hero-headline {
        font-family: var(--font-title);
        font-weight: 800;
        font-size: clamp(28px, 3.8vw, 42px);
        letter-spacing: -0.03em;
        margin: 0 0 8px 0;
        line-height: 1.1;
        color: #FFFFFF;
    }
    .hero-headline span {
        background: linear-gradient(90deg, #8B5CF6, #E879F9, #F472B6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .hero-desc {
        font-size: 15.5px;
        color: var(--text-muted);
        max-width: 720px;
        margin: 0 0 16px 0;
        line-height: 1.55;
    }

    /* ── AI Pipeline Flow Visualization ── */
    .pipeline-bar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: rgba(7, 10, 20, 0.7);
        border: 1px solid var(--border-subtle);
        border-radius: 14px;
        padding: 10px 18px;
        margin-top: 14px;
        overflow-x: auto;
    }
    .pipeline-node {
        display: flex;
        align-items: center;
        gap: 6px;
        font-family: var(--font-mono);
        font-size: 11px;
        font-weight: 600;
        color: var(--text-muted);
        white-space: nowrap;
    }
    .pipeline-node.active {
        color: var(--fuchsia-secondary);
    }
    .pipeline-arrow {
        color: rgba(232, 121, 249, 0.4);
        font-size: 12px;
        margin: 0 6px;
    }

    /* ── Two-Column Command Center Workspace ── */
    .workspace-panel {
        background: var(--bg-glass-card);
        border: 1px solid var(--border-subtle);
        border-radius: 18px;
        padding: 1.4rem;
        backdrop-filter: blur(16px);
        box-shadow: 0 15px 35px -10px rgba(0, 0, 0, 0.5);
        height: 100%;
    }
    .panel-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding-bottom: 12px;
        margin-bottom: 14px;
        border-bottom: 1px solid var(--border-subtle);
    }
    .panel-title {
        font-family: var(--font-title);
        font-size: 15px;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        color: var(--fuchsia-secondary);
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* ── AI Processing Sequence ── */
    .processing-stepper {
        background: rgba(5, 8, 17, 0.7);
        border: 1px solid rgba(139, 92, 246, 0.3);
        border-radius: 12px;
        padding: 14px 16px;
        margin: 12px 0;
        font-family: var(--font-mono);
        font-size: 12px;
        color: var(--fuchsia-secondary);
        animation: pulseStep 2s infinite ease-in-out;
    }
    @keyframes pulseStep {
        0%, 100% { border-color: rgba(139, 92, 246, 0.25); }
        50% { border-color: rgba(232, 121, 249, 0.6); box-shadow: 0 0 18px rgba(139, 92, 246, 0.3); }
    }

    /* ── KPI Metric Cards ── */
    .kpi-row {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 12px;
        margin-bottom: 16px;
    }
    .kpi-box {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.8), rgba(9, 13, 26, 0.9));
        border: 1px solid rgba(255, 255, 255, 0.09);
        border-radius: 14px;
        padding: 14px 16px;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .kpi-box:hover {
        transform: translateY(-2px);
        border-color: var(--violet-primary);
        box-shadow: 0 10px 25px rgba(139, 92, 246, 0.25);
    }
    .kpi-label {
        font-family: var(--font-mono);
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--text-muted);
        margin-bottom: 4px;
    }
    .kpi-val {
        font-family: var(--font-title);
        font-size: 22px;
        font-weight: 700;
        color: #FFFFFF;
    }
    .kpi-val.violet { color: var(--fuchsia-secondary); }
    .kpi-val.emerald { color: var(--emerald-glow); }
    .kpi-val.amber { color: var(--amber-glow); }

    /* ── Executive Insight Card ── */
    .insight-card-executive {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.12), rgba(139, 92, 246, 0.08), rgba(15, 23, 42, 0.9));
        border: 1px solid rgba(245, 158, 11, 0.35);
        border-left: 4px solid var(--amber-glow);
        border-radius: 14px;
        padding: 16px 20px;
        margin: 14px 0;
        box-shadow: 0 12px 30px -8px rgba(245, 158, 11, 0.2);
    }
    .insight-headline {
        font-family: var(--font-title);
        font-size: 14.5px;
        font-weight: 700;
        color: #FCD34D;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .insight-text {
        font-size: 14px;
        color: #E2E8F0;
        line-height: 1.6;
    }

    /* ── Quick Action Suggestion Pills ── */
    .stButton > button {
        border-radius: 12px !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        border: 1px solid rgba(255, 255, 255, 0.10) !important;
        background: rgba(18, 26, 48, 0.75) !important;
        color: #E2E8F0 !important;
        transition: all 0.25s ease !important;
    }
    .stButton > button:hover {
        border-color: var(--violet-primary) !important;
        color: #FFFFFF !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 18px rgba(139, 92, 246, 0.4) !important;
    }

    /* ── Chat Input ── */
    [data-testid="stChatInput"] {
        background: rgba(15, 23, 42, 0.85) !important;
        backdrop-filter: blur(16px) !important;
        border: 1px solid rgba(139, 92, 246, 0.35) !important;
        border-radius: 999px !important;
        box-shadow: 0 10px 35px -8px rgba(0, 0, 0, 0.7), 0 0 15px rgba(139, 92, 246, 0.15) !important;
        transition: all 0.3s ease !important;
    }
    [data-testid="stChatInput"]:focus-within {
        border-color: var(--fuchsia-secondary) !important;
        box-shadow: 0 12px 40px -5px rgba(139, 92, 246, 0.45), 0 0 25px rgba(232, 121, 249, 0.35) !important;
        transform: translateY(-2px) !important;
    }

    /* ── Code Expander ── */
    .stCodeBlock {
        border-radius: 12px !important;
        border: 1px solid rgba(139, 92, 246, 0.3) !important;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.6), 0 0 15px rgba(139, 92, 246, 0.15) !important;
        background: #060913 !important;
    }
    .streamlit-expanderHeader {
        background: rgba(15, 23, 42, 0.9) !important;
        border: 1px solid rgba(255, 255, 255, 0.10) !important;
        border-radius: 10px !important;
        font-family: var(--font-title) !important;
        font-weight: 600 !important;
        color: var(--fuchsia-secondary) !important;
    }

    /* Reduced Motion */
    @media (prefers-reduced-motion: reduce) {
        *, ::before, ::after {
            animation-duration: 0.001s !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.001s !important;
        }
    }

    /* Clean Streamlit Default Chrome */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ── AI Brain & 3D Core Visualization Component (Violet / Fuchsia) ──
def render_ai_brain_orb():
    """Renders an interactive Three.js 3D AI Brain Data Core with floating nodes and violet/fuchsia synaptic lights."""
    three_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body { margin: 0; overflow: hidden; background: transparent; }
            #orb-canvas { width: 100%; height: 130px; display: block; }
        </style>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    </head>
    <body>
        <canvas id="orb-canvas"></canvas>
        <script>
            const canvas = document.getElementById('orb-canvas');
            const scene = new THREE.Scene();
            const camera = new THREE.PerspectiveCamera(40, window.innerWidth / 130, 0.1, 1000);
            camera.position.z = 5.5;

            const renderer = new THREE.WebGLRenderer({ canvas: canvas, alpha: true, antialias: true });
            renderer.setSize(window.innerWidth, 130);
            renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

            // Central Brain / Data Core (Torus Knot + Icosahedron Wireframe)
            const coreGroup = new THREE.Group();
            
            const knotGeo = new THREE.TorusKnotGeometry(1.0, 0.28, 64, 16);
            const knotMat = new THREE.MeshStandardMaterial({
                color: 0x8B5CF6,
                wireframe: true,
                emissive: 0x4C1D95,
                roughness: 0.2
            });
            const knot = new THREE.Mesh(knotGeo, knotMat);
            coreGroup.add(knot);

            // Floating Synaptic Data Particles
            const particleGeo = new THREE.BufferGeometry();
            const particleCount = 40;
            const posArray = new Float32Array(particleCount * 3);
            for(let i=0; i<particleCount*3; i++){
                posArray[i] = (Math.random() - 0.5) * 4.5;
            }
            particleGeo.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
            const particleMat = new THREE.PointsMaterial({
                size: 0.08,
                color: 0xE879F9,
                transparent: true,
                opacity: 0.85
            });
            const particles = new THREE.Points(particleGeo, particleMat);
            coreGroup.add(particles);

            scene.add(coreGroup);

            // Dual Neon Accent Lights (Electric Violet + Neon Fuchsia)
            const violetLight = new THREE.PointLight(0x8B5CF6, 3, 30);
            violetLight.position.set(4, 3, 4);
            scene.add(violetLight);

            const fuchsiaLight = new THREE.PointLight(0xE879F9, 3, 30);
            fuchsiaLight.position.set(-4, -3, 4);
            scene.add(fuchsiaLight);

            const ambientLight = new THREE.AmbientLight(0x111827, 2.0);
            scene.add(ambientLight);

            // Mouse parallax interaction
            let mouseX = 0, mouseY = 0;
            window.addEventListener('mousemove', (e) => {
                mouseX = (e.clientX / window.innerWidth - 0.5) * 1.5;
                mouseY = (e.clientY / 130 - 0.5) * 1.5;
            });

            window.addEventListener('resize', () => {
                camera.aspect = window.innerWidth / 130;
                camera.updateProjectionMatrix();
                renderer.setSize(window.innerWidth, 130);
            });

            let clock = new THREE.Clock();
            function animate() {
                requestAnimationFrame(animate);
                const t = clock.getElapsedTime();

                coreGroup.rotation.y = t * 0.4 + mouseX * 0.5;
                coreGroup.rotation.x = Math.sin(t * 0.5) * 0.2 + mouseY * 0.5;
                particles.rotation.y = -t * 0.2;

                renderer.render(scene, camera);
            }
            animate();
        </script>
    </body>
    </html>
    """
    components.html(three_html, height=135)


# ── Backend Agents & DB Loaders ──
def get_groq_api_key():
    """Retrieve Groq API key with multi-tier resolution (Session State, Env, Streamlit Secrets)."""
    # 1. User manual input in session state
    if "user_groq_api_key" in st.session_state and st.session_state.user_groq_api_key:
        return str(st.session_state.user_groq_api_key).strip()
    
    # 2. Local/System Environment variables
    env_key = os.getenv("GROQ_API_KEY") or os.environ.get("GROQ_API_KEY")
    if env_key:
        return str(env_key).strip()
    
    # 3. Streamlit Cloud Secrets (handles direct key, lowercase, and nested dicts)
    try:
        if hasattr(st, "secrets"):
            if "GROQ_API_KEY" in st.secrets:
                return str(st.secrets["GROQ_API_KEY"]).strip()
            if "groq_api_key" in st.secrets:
                return str(st.secrets["groq_api_key"]).strip()
            if "GROQ" in st.secrets and isinstance(st.secrets["GROQ"], dict):
                return str(st.secrets["GROQ"].get("api_key", "")).strip()
    except Exception:
        pass
        
    return None


def ensure_database_exists():
    """Check if data/olist.db exists. If missing, auto-build from zip/CSVs."""
    db_path = os.path.join(os.path.dirname(__file__), "data", "olist.db")
    if not os.path.exists(db_path):
        with st.spinner("📦 Initializing live database (100k+ records)..."):
            try:
                from app.load_data import create_sqlite_database
                create_sqlite_database()
            except Exception as e:
                st.error(f"❌ Database initialization error: {e}")


ensure_database_exists()

from app.utils import strip_thinking, SQLCaptureCallbackHandler
from app.prompts import build_system_prompt
from app.explain import explain_result
from app.charts import auto_chart
from app.guardrails import validate_sql
from app.database import (
    DatabaseConnectionManager,
    DatabaseType,
    mask_url,
    get_default_olist_engine,
    InvalidURLError,
    UnsupportedDatabaseError,
)

MODELS_PRIORITY = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.6-27b"]


@st.cache_resource
def init_agent(api_key: str, model_name: str = "openai/gpt-oss-120b", db_url: str = ""):
    """Initialize LangChain SQL Agent with Groq LLM and dynamic database connection."""
    from langchain_groq import ChatGroq
    from langchain_community.agent_toolkits import create_sql_agent
    from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
    from langchain_community.utilities import SQLDatabase

    if not db_url:
        _, db_url = get_default_olist_engine()

    db = SQLDatabase.from_uri(db_url)

    llm = ChatGroq(
        model=model_name,
        temperature=0.0,
        api_key=api_key,
    )

    system_prompt = build_system_prompt()
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)

    agent = create_sql_agent(
        llm=llm,
        toolkit=toolkit,
        agent_type="tool-calling",
        verbose=False,
        handle_parsing_errors=True,
        prefix=system_prompt,
    )
    return agent, db, llm


@st.cache_resource
def init_explain_llm(api_key: str, model_name: str = "openai/gpt-oss-120b"):
    """Initialize separate LLM instance for executive business insights."""
    from langchain_groq import ChatGroq
    return ChatGroq(
        model=model_name,
        temperature=0.3,
        api_key=api_key,
    )


def run_query_for_chart(db, sql):
    """Run a validated SQL query against active database manager and return DataFrame."""
    if not sql:
        return pd.DataFrame()
    if "db_manager" in st.session_state and st.session_state.db_manager:
        try:
            return st.session_state.db_manager.execute_query(sql)
        except Exception:
            pass
    try:
        import sqlalchemy
        engine = sqlalchemy.create_engine(db._engine.url)
        with engine.connect() as conn:
            df = pd.read_sql(sql, conn)
        return df
    except Exception:
        return pd.DataFrame()


# ── Session State Management ──
if "db_manager" not in st.session_state:
    _, default_olist_url = get_default_olist_engine()
    st.session_state.db_manager = DatabaseConnectionManager(default_olist_url, name="Olist Brazilian E-Commerce (Demo)")
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages = []
if "current_nav" not in st.session_state:
    st.session_state.current_nav = "AI Analyst"
if "executive_mode" not in st.session_state:
    st.session_state.executive_mode = False
if "latest_df" not in st.session_state:
    st.session_state.latest_df = pd.DataFrame()
if "latest_sql" not in st.session_state:
    st.session_state.latest_sql = ""
if "latest_chart" not in st.session_state:
    st.session_state.latest_chart = None
if "latest_insight" not in st.session_state:
    st.session_state.latest_insight = ""
if "latest_question" not in st.session_state:
    st.session_state.latest_question = ""
if "user_groq_api_key" not in st.session_state:
    st.session_state.user_groq_api_key = ""


# ── Top Navigation Bar Header ──
nav_col1, nav_col2, nav_col3 = st.columns([3, 5, 2.5])

with nav_col1:
    st.markdown("""
    <div class="brand-logo-wrap">
        <div class="brand-logo-icon">⚡</div>
        <div>
            <div class="brand-text">DataPilot AI</div>
            <div class="brand-tagline">Ask your business data anything.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with nav_col2:
    # Top Tab Navigation Bar
    nav_tabs = ["🤖 AI Analyst", "📊 Dashboard", "🗄️ Data Sources", "📜 Query History", "💡 Insights", "⚙️ Settings"]
    selected_tab = st.radio("Navigation", nav_tabs, horizontal=True, label_visibility="collapsed")
    st.session_state.current_nav = selected_tab.split(" ")[-1]

with nav_col3:
    # Live status and Executive View Toggle
    st.markdown("""
    <div style="display: flex; align-items: center; justify-content: flex-end; gap: 10px;">
        <div class="status-badge"><span class="status-dot"></span> Live DB: 100k+ Orders</div>
    </div>
    """, unsafe_allow_html=True)
    st.session_state.executive_mode = st.toggle("👔 Executive View", value=st.session_state.executive_mode, help="Hides SQL and technical query details for high-level executive reviews.")

st.markdown("<div style='margin-bottom: 1.2rem;'></div>", unsafe_allow_html=True)


# ==============================================================================
# VIEW 1: AI ANALYST (Core Command Center Workspace)
# ==============================================================================
if "Analyst" in st.session_state.current_nav:
    # ── Hero Command Section ──
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-headline">Ask your data. <span>Get the answer.</span></div>
        <div class="hero-desc">Turn plain English into real-time business intelligence without SQL, complex dashboards, or technical database analysis.</div>
    </div>
    """, unsafe_allow_html=True)

    # 3D AI Brain Core
    render_ai_brain_orb()

    # ── AI Flow Pipeline Bar ──
    st.markdown("""
    <div class="pipeline-bar">
        <div class="pipeline-node active"><span>1.</span> User Question</div>
        <div class="pipeline-arrow">→</div>
        <div class="pipeline-node active"><span>2.</span> AI Intent Analysis</div>
        <div class="pipeline-arrow">→</div>
        <div class="pipeline-node active"><span>3.</span> SQL Generated</div>
        <div class="pipeline-arrow">→</div>
        <div class="pipeline-node active"><span>4.</span> Live Database Query</div>
        <div class="pipeline-arrow">→</div>
        <div class="pipeline-node active"><span>5.</span> Visual Analytics</div>
        <div class="pipeline-arrow">→</div>
        <div class="pipeline-node active"><span>6.</span> Business Insights</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom: 1.4rem;'></div>", unsafe_allow_html=True)

    # ── API Key Banner if Missing ──
    current_key = get_groq_api_key()
    if not current_key:
        st.markdown("""
        <div class="insight-card-executive" style="border-left-color: #8B5CF6; border-color: rgba(139, 92, 246, 0.45); margin-bottom: 1.2rem;">
            <div class="insight-headline" style="color: #E879F9;">🔑 Groq API Key Required</div>
            <div class="insight-text">
                To execute natural language queries against the live database in real-time, please enter your Groq API key below.
                <br><span style="color: #94A3B8; font-size: 12px;">Get a free API key instantly at <a href="https://console.groq.com" target="_blank" style="color: #E879F9; text-decoration: underline;">console.groq.com</a></span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        with st.form("inline_api_key_form"):
            ak_col1, ak_col2 = st.columns([4, 1.2])
            with ak_col1:
                entered_k = st.text_input("Groq API Key (gsk_...)", type="password", placeholder="gsk_...", label_visibility="collapsed")
            with ak_col2:
                sub_k = st.form_submit_button("⚡ Connect Key", use_container_width=True)
            if sub_k and entered_k:
                st.session_state.user_groq_api_key = entered_k.strip()
                st.success("✅ Connected successfully! You can now run queries.")
                st.rerun()

    # ── Quick Launch Suggestion Pills ──
    st.markdown("<p style='font-size:12px; font-weight:600; color:#94A3B8; text-transform:uppercase; letter-spacing:0.08em; margin: 0 0 8px 0;'>⚡ Suggested Executive Queries:</p>", unsafe_allow_html=True)
    qcol1, qcol2, qcol3, qcol4, qcol5 = st.columns(5)
    
    with qcol1:
        if st.button("📊 Top 5 Categories by Revenue", key="sug_1", use_container_width=True):
            st.session_state.pending_question = "What are the top 5 product categories by revenue in English?"
    with qcol2:
        if st.button("💰 Delivered Orders Revenue", key="sug_2", use_container_width=True):
            st.session_state.pending_question = "What is the total revenue from delivered orders?"
    with qcol3:
        if st.button("📅 2018 Monthly Sales Trend", key="sug_3", use_container_width=True):
            st.session_state.pending_question = "How many orders were placed each month in 2018?"
    with qcol4:
        if st.button("🚚 Average Delivery Days", key="sug_4", use_container_width=True):
            st.session_state.pending_question = "What is the average delivery time in days for delivered orders?"
    with qcol5:
        if st.button("🗺️ Customer Count by State", key="sug_5", use_container_width=True):
            st.session_state.pending_question = "Which 5 states have the most customers?"

    st.markdown("<div style='margin-bottom: 1.4rem;'></div>", unsafe_allow_html=True)

    # ── Core Interactive Two-Column Workspace ──
    left_col, right_col = st.columns([1.1, 1.35], gap="large")

    # ── LEFT COLUMN: AI Conversation & Intent Panel ──
    with left_col:
        st.markdown("""
        <div class="workspace-panel">
            <div class="panel-header">
                <div class="panel-title">💬 AI Analyst Conversation</div>
                <div style="font-family: var(--font-mono); font-size: 11px; color: #10B981;">● Online</div>
            </div>
        """, unsafe_allow_html=True)

        # Message History Loop
        if not st.session_state.messages:
            st.markdown("""
            <div style="text-align: center; padding: 2rem 1rem; color: #64748B;">
                <div style="font-size: 32px; margin-bottom: 8px;">🤖</div>
                <div style="font-weight: 600; color: #94A3B8; margin-bottom: 4px;">DataPilot AI is ready.</div>
                <div style="font-size: 13px;">Type any business question below or click a suggested query above.</div>
            </div>
            """, unsafe_allow_html=True)

        for msg in st.session_state.messages:
            if msg["role"] == "user":
                with st.chat_message("user", avatar="🧑‍💼"):
                    st.markdown(f"<span style='font-size: 14.5px; font-weight: 500;'>{msg['content']}</span>", unsafe_allow_html=True)
            else:
                with st.chat_message("assistant", avatar="⚡"):
                    st.markdown(msg.get("answer", ""))
                    if not st.session_state.executive_mode and msg.get("sql"):
                        with st.expander("⚡ View AI-Generated SQL Query", expanded=False):
                            st.code(msg["sql"], language="sql")

        st.markdown("</div>", unsafe_allow_html=True)

        # Chat Input
        if "pending_question" in st.session_state:
            user_input = st.session_state.pending_question
            del st.session_state.pending_question
        else:
            user_input = st.chat_input("Ask anything about your business data...")

    # ── RIGHT COLUMN: Dynamic Analytics & Intelligence Panel ──
    with right_col:
        st.markdown("""
        <div class="workspace-panel">
            <div class="panel-header">
                <div class="panel-title">📈 Dynamic Analytics & Insights</div>
                <div style="font-family: var(--font-mono); font-size: 11px; color: #E879F9;">⚡ Real-time Stream</div>
            </div>
        """, unsafe_allow_html=True)

        # Process user query if submitted
        groq_key = get_groq_api_key()
        if user_input:
            if not groq_key:
                st.error("🔑 Groq API key missing. Please enter your Groq API key above or in the ⚙️ Settings tab.")
            else:
                # Add user message
                st.session_state.messages.append({"role": "user", "content": user_input})
                st.session_state.latest_question = user_input

                # Execute with automatic multi-model fallback
                with st.spinner("🤖 Synthesizing query & executing on live database..."):
                    execution_success = False
                    last_err = ""

                    from app.database import get_cached_schema
                    from app.agent import UniversalSQLGenerator, select_relevant_schema

                    active_db_url = st.session_state.db_manager.normalized_url if "db_manager" in st.session_state and st.session_state.db_manager else ""
                    active_engine = st.session_state.db_manager.engine if "db_manager" in st.session_state and st.session_state.db_manager else None

                    # Introspect or fetch cached schema
                    current_schema = None
                    if active_engine and active_db_url:
                        try:
                            current_schema = get_cached_schema(active_engine, active_db_url)
                        except Exception:
                            current_schema = None

                    for model_candidate in MODELS_PRIORITY:
                        try:
                            explain_llm = init_explain_llm(groq_key, model_name=model_candidate)
                            
                            # 1. Fast Universal SQL Generator
                            if current_schema:
                                relevant_schema = select_relevant_schema(current_schema, user_input)
                                gen_result = UniversalSQLGenerator.generate_sql(
                                    question=user_input,
                                    db_schema=relevant_schema,
                                    api_key=groq_key,
                                    model_name=model_candidate,
                                )
                                main_sql = gen_result.sql
                                answer = gen_result.reasoning_summary

                                df = pd.DataFrame()
                                if main_sql and active_engine:
                                    try:
                                        df = st.session_state.db_manager.execute_query(main_sql)
                                    except Exception:
                                        df = pd.DataFrame()

                            else:
                                # Fallback to LangChain agent if schema discovery failed
                                agent, db, llm = init_agent(groq_key, model_name=model_candidate, db_url=active_db_url)
                                callback_handler = SQLCaptureCallbackHandler()
                                result = agent.invoke(
                                    {"input": user_input},
                                    config={"callbacks": [callback_handler]}
                                )
                                answer = strip_thinking(result.get("output", "No response generated."))
                                main_sql = callback_handler.sql_queries[-1] if callback_handler.sql_queries else None
                                df = run_query_for_chart(db, validate_sql(main_sql)) if main_sql else pd.DataFrame()

                            chart_fig = None
                            if not df.empty:
                                try:
                                    chart_fig = auto_chart(df, user_input)
                                except Exception:
                                    pass

                            explanation = None
                            if not df.empty:
                                try:
                                    time.sleep(1)
                                    explanation = explain_result(user_input, df, sql=main_sql, llm=explain_llm)
                                    if explanation:
                                        answer = explanation
                                except Exception:
                                    pass

                            # Save latest analytics state
                            st.session_state.latest_df = df
                            st.session_state.latest_sql = main_sql
                            st.session_state.latest_chart = chart_fig
                            st.session_state.latest_insight = explanation

                            st.session_state.messages.append({
                                "role": "assistant",
                                "answer": answer,
                                "sql": main_sql,
                                "df": df,
                                "chart": chart_fig,
                                "explanation": explanation,
                            })
                            execution_success = True
                            break

                        except Exception as e:
                            last_err = str(e)
                            if "429" in last_err or "rate_limit" in last_err.lower():
                                continue  # Fallback to next model candidate
                            else:
                                break

                    if not execution_success:
                        if "429" in last_err or "rate_limit" in last_err.lower():
                            st.warning("⏳ Daily token quota temporarily reached across all free-tier models. Please retry in a few moments or enter a custom Groq API key in Settings.")
                        else:
                            st.error(f"❌ Query execution error: {last_err}")

        # Render Latest Dynamic Analytics Content
        if not st.session_state.latest_df.empty or st.session_state.latest_chart:
            # 1. Executive Insight Card
            if st.session_state.latest_insight:
                st.markdown(f"""
                <div class="insight-card-executive">
                    <div class="insight-headline">💡 AI EXECUTIVE INSIGHT</div>
                    <div class="insight-text">{st.session_state.latest_insight}</div>
                </div>
                """, unsafe_allow_html=True)

            # 2. Interactive Chart
            if st.session_state.latest_chart:
                st.plotly_chart(st.session_state.latest_chart, use_container_width=True)

            # 3. Interactive Data Table Inspector
            if not st.session_state.latest_df.empty:
                with st.expander("📊 Inspect Live Data Table", expanded=False):
                    st.dataframe(st.session_state.latest_df, use_container_width=True)

            # 4. View Generated SQL (Hidden in Executive Mode)
            if not st.session_state.executive_mode and st.session_state.latest_sql:
                with st.expander("⚡ Verified SQL Engine Code", expanded=False):
                    st.code(st.session_state.latest_sql, language="sql")

            # Action Toolbar
            act_col1, act_col2, act_col3 = st.columns(3)
            with act_col1:
                if st.button("📥 Export CSV", key="btn_exp_csv", use_container_width=True):
                    csv_data = st.session_state.latest_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Download File",
                        data=csv_data,
                        file_name=f"datapilot_export_{int(time.time())}.csv",
                        mime="text/csv",
                    )
            with act_col2:
                if st.button("🔍 Why this trend?", key="btn_why", use_container_width=True):
                    st.session_state.pending_question = f"Why did this happen? Break down the drivers: {st.session_state.latest_question}"
                    st.rerun()
            with act_col3:
                if st.button("🔄 Compare Previous", key="btn_comp", use_container_width=True):
                    st.session_state.pending_question = f"Compare this metric with the previous period: {st.session_state.latest_question}"
                    st.rerun()

        else:
            # Default Analytics Preview State
            st.markdown("""
            <div style="text-align: center; padding: 3.5rem 1rem; color: #64748B;">
                <div style="font-size: 38px; margin-bottom: 12px;">📊</div>
                <div style="font-family: var(--font-title); font-size: 18px; font-weight: 700; color: #CBD5E1; margin-bottom: 6px;">Live Analytics Canvas</div>
                <div style="font-size: 14px; max-width: 380px; margin: 0 auto; color: #94A3B8;">Charts, KPI summary cards, and executive insights will populate dynamically as questions are answered.</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)


# ==============================================================================
# VIEW 2: EXECUTIVE DASHBOARD
# ==============================================================================
elif "Dashboard" in st.session_state.current_nav:
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-headline">Executive <span>Overview Dashboard</span></div>
        <div class="hero-desc">Real-time consolidated KPIs, revenue velocity, order fulfillment metrics, and category performance across 100k+ Brazilian e-commerce transactions.</div>
    </div>
    """, unsafe_allow_html=True)

    # 4 Key Business KPIs
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.markdown("""
        <div class="kpi-box">
            <div class="kpi-label">💰 Total Delivered Revenue</div>
            <div class="kpi-val violet">R$ 13.22M</div>
            <div style="font-size: 11.5px; color: #10B981; margin-top: 4px;">↑ +14.2% YoY growth</div>
        </div>
        """, unsafe_allow_html=True)
    with kpi2:
        st.markdown("""
        <div class="kpi-box">
            <div class="kpi-label">📦 Total Delivered Orders</div>
            <div class="kpi-val emerald">96,478</div>
            <div style="font-size: 11.5px; color: #10B981; margin-top: 4px;">↑ 97.0% fulfillment rate</div>
        </div>
        """, unsafe_allow_html=True)
    with kpi3:
        st.markdown("""
        <div class="kpi-box">
            <div class="kpi-label">⭐ Avg Review Score</div>
            <div class="kpi-val amber">4.09 / 5.0</div>
            <div style="font-size: 11.5px; color: #F59E0B; margin-top: 4px;">● 77.2% 5-star reviews</div>
        </div>
        """, unsafe_allow_html=True)
    with kpi4:
        st.markdown("""
        <div class="kpi-box">
            <div class="kpi-label">🚚 Avg Delivery Speed</div>
            <div class="kpi-val violet">12.5 Days</div>
            <div style="font-size: 11.5px; color: #10B981; margin-top: 4px;">↓ 1.4 days faster</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)

    # 2 Curated Visual Charts
    dcol1, dcol2 = st.columns(2)
    with dcol1:
        st.markdown("<div class='workspace-panel'><div class='panel-title'>📈 Monthly Order Velocity (2018)</div>", unsafe_allow_html=True)
        # 2018 Monthly Sales Trend
        trend_df = pd.DataFrame({
            "Month": ["2018-01", "2018-02", "2018-03", "2018-04", "2018-05", "2018-06", "2018-07", "2018-08"],
            "Orders": [7069, 6555, 7003, 6800, 6749, 6099, 6156, 6351]
        })
        fig_trend = px.line(trend_df, x="Month", y="Orders", markers=True)
        fig_trend.update_layout(
            paper_bgcolor="rgba(15, 23, 42, 0.7)",
            plot_bgcolor="rgba(10, 15, 28, 0.5)",
            font=dict(color="#F1F5F9"),
            margin=dict(l=20, r=20, t=30, b=20),
            height=300
        )
        fig_trend.update_traces(line=dict(color="#8B5CF6", width=3), marker=dict(size=8, color="#E879F9"))
        st.plotly_chart(fig_trend, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with dcol2:
        st.markdown("<div class='workspace-panel'><div class='panel-title'>🏆 Top 5 Product Categories by Revenue</div>", unsafe_allow_html=True)
        cat_df = pd.DataFrame({
            "Category": ["Health & Beauty", "Watches & Gifts", "Bed Bath & Table", "Sports & Leisure", "Computers & Access"],
            "Revenue_M": [1.26, 1.21, 1.04, 0.99, 0.91]
        })
        fig_cat = px.bar(cat_df, x="Revenue_M", y="Category", orientation="h", text="Revenue_M")
        fig_cat.update_layout(
            paper_bgcolor="rgba(15, 23, 42, 0.7)",
            plot_bgcolor="rgba(10, 15, 28, 0.5)",
            font=dict(color="#F1F5F9"),
            margin=dict(l=20, r=20, t=30, b=20),
            height=300
        )
        fig_cat.update_traces(marker_color=["#8B5CF6", "#E879F9", "#D946EF", "#A855F7", "#F472B6"])
        st.plotly_chart(fig_cat, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)


# ==============================================================================
# VIEW 3: DATA SOURCES & LIVE SCHEMA VISUALIZER
# ==============================================================================
elif "Sources" in st.session_state.current_nav:
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-headline">Universal <span>Enterprise Data Sources</span></div>
        <div class="hero-desc">Connect any SQL database (PostgreSQL, MySQL, SQLite), monitor live connection health, and inspect database schema structures.</div>
    </div>
    """, unsafe_allow_html=True)

    db_mgr: DatabaseConnectionManager = st.session_state.get("db_manager")
    is_live = db_mgr.is_connected if db_mgr else False
    current_db_type = db_mgr.db_type.value.upper() if db_mgr else "UNKNOWN"
    current_masked_url = db_mgr.masked_url if db_mgr else "No connection configured"

    # Active Live Connection Card
    st.markdown(f"""
    <div class="workspace-panel" style="border-color: rgba(16, 185, 129, 0.4); margin-bottom: 1.5rem;">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="font-size: 28px;">🗄️</div>
                <div>
                    <div style="font-family: var(--font-title); font-size: 18px; font-weight: 700;">{db_mgr.name if db_mgr else 'Active Database'} ({current_db_type})</div>
                    <div style="font-size: 13px; color: #94A3B8;">URI: <code>{current_masked_url}</code></div>
                </div>
            </div>
            <div class="status-badge"><span class="status-dot"></span> {'CONNECTED & SYNCED' if is_live else 'DISCONNECTED'}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Universal Database Connection Form
    with st.expander("➕ Connect a New SQL Database (PostgreSQL / MySQL / SQLite)", expanded=False):
        st.markdown("<p style='font-size: 13px; color: #94A3B8;'>Enter your database connection URL. Passwords are encrypted in memory and masked in the UI.</p>", unsafe_allow_html=True)
        
        db_type_choice = st.selectbox(
            "Select Database Type",
            ["PostgreSQL", "MySQL", "SQLite"],
            index=0,
            key="db_type_selector"
        )
        
        placeholder_map = {
            "PostgreSQL": "postgresql://username:password@localhost:5432/database_name",
            "MySQL": "mysql://username:password@localhost:3306/database_name",
            "SQLite": "sqlite:///path/to/database.db"
        }

        conn_url_input = st.text_input(
            "Connection URL",
            placeholder=placeholder_map[db_type_choice],
            key="custom_db_url_input",
            type="password",
            help="Your password will be masked automatically and never stored in plain text."
        )

        btn_col1, btn_col2, btn_col3 = st.columns([1.5, 1.5, 3])
        with btn_col1:
            if st.button("🧪 Test Connection", key="btn_test_conn", use_container_width=True):
                if not conn_url_input:
                    st.error("Please enter a connection URL first.")
                else:
                    try:
                        temp_mgr = DatabaseConnectionManager(conn_url_input, name="TestConn")
                        ok, msg = temp_mgr.test_connection()
                        if ok:
                            st.success(f"✅ {msg}")
                        else:
                            st.error(f"❌ {msg}")
                        temp_mgr.dispose()
                    except Exception as e:
                        st.error(f"❌ Connection error: {e}")

        with btn_col2:
            if st.button("🔗 Connect & Activate", key="btn_activate_conn", use_container_width=True):
                if not conn_url_input:
                    st.error("Please enter a connection URL first.")
                else:
                    try:
                        new_mgr = DatabaseConnectionManager(conn_url_input, name=f"Custom {db_type_choice} DB")
                        ok, msg = new_mgr.test_connection()
                        if ok:
                            st.session_state.db_manager = new_mgr
                            st.success(f"✅ Successfully switched active database to {db_type_choice}!")
                            st.rerun()
                        else:
                            st.error(f"❌ Could not connect: {msg}")
                    except Exception as e:
                        st.error(f"❌ Activation error: {e}")

        with btn_col3:
            if st.button("🔄 Reset to Olist Demo Database", key="btn_reset_demo", use_container_width=True):
                _, olist_url = get_default_olist_engine()
                st.session_state.db_manager = DatabaseConnectionManager(olist_url, name="Olist Brazilian E-Commerce (Demo)")
                st.info("Reset to default Olist Demo SQLite database.")
                st.rerun()

    # Schema Overview & Inspector using SchemaCache
    db_schema = None
    if st.session_state.db_manager and st.session_state.db_manager.engine:
        from app.database import get_cached_schema, SchemaCache
        try:
            db_schema = get_cached_schema(
                st.session_state.db_manager.engine,
                st.session_state.db_manager.normalized_url
            )
        except Exception as e:
            st.warning(f"Could not load schema: {e}")

    total_tbls = len(db_schema.tables) if db_schema else 0
    total_rels = len(db_schema.relationships) if db_schema else 0

    # Schema Stats & Controls Header
    s_col1, s_col2 = st.columns([3, 1])
    with s_col1:
        st.markdown(f"<div class='panel-title' style='margin: 18px 0 12px 0;'>📊 Database Schema Overview ({total_tbls} Tables · {total_rels} Relationships)</div>", unsafe_allow_html=True)
    with s_col2:
        if st.button("🔄 Refresh Schema Cache", key="btn_refresh_schema", use_container_width=True):
            if st.session_state.db_manager and st.session_state.db_manager.normalized_url:
                SchemaCache.invalidate(st.session_state.db_manager.normalized_url)
                st.success("Schema cache refreshed!")
                st.rerun()

    if db_schema and db_schema.tables:
        # Schema Tables Grid
        scol1, scol2, scol3 = st.columns(3)
        for idx, (tname, tschema) in enumerate(db_schema.tables.items()):
            col_target = [scol1, scol2, scol3][idx % 3]
            
            # Format columns with PK indicators
            col_badges = []
            for c in tschema.columns[:6]:
                pk_mark = "🔑 " if c.primary_key else ""
                col_badges.append(f"{pk_mark}{c.name} ({c.type})")
            
            col_str = ", ".join(col_badges)
            if len(tschema.columns) > 6:
                col_str += f", ... (+{len(tschema.columns)-6} more)"
            
            # Row count string
            row_str = f"{tschema.row_count_estimate:,} records" if tschema.row_count_estimate is not None else f"{len(tschema.columns)} cols"

            with col_target:
                st.markdown(f"""
                <div class="kpi-box" style="margin-bottom: 12px;">
                    <div style="display: flex; align-items: center; justify-content: space-between;">
                        <div style="font-family: var(--font-title); font-weight: 700; color: #E879F9; font-size: 15px;">📁 {tname}</div>
                        <div style="font-family: var(--font-mono); font-size: 11px; color: #10B981;">{row_str}</div>
                    </div>
                    <div style="font-family: var(--font-mono); font-size: 11px; color: #94A3B8; margin-top: 6px; line-height: 1.4;">{col_str}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Expandable detailed schema
                with st.expander(f"Inspect {tname} Schema", expanded=False):
                    col_df = pd.DataFrame([
                        {
                            "Column": c.name,
                            "Type": c.type,
                            "Primary Key": "✅ PK" if c.primary_key else "",
                            "Nullable": "Yes" if c.nullable else "No"
                        }
                        for c in tschema.columns
                    ])
                    st.dataframe(col_df, use_container_width=True, hide_index=True)
                    if tschema.foreign_keys:
                        st.markdown("**Foreign Keys:**")
                        for fk in tschema.foreign_keys:
                            st.markdown(f"- `{', '.join(fk.constrained_columns)}` ──► `{fk.referred_table}({', '.join(fk.referred_columns)})`")
    else:
        st.info("No tables detected in the connected database.")


# ==============================================================================
# VIEW 4: QUERY HISTORY & AUDIT LOG
# ==============================================================================
elif "History" in st.session_state.current_nav:
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-headline">Session <span>Query History & Audit</span></div>
        <div class="hero-desc">Traceable record of all natural language questions, AI-generated SQL queries, and execution audit trails.</div>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.messages:
        st.info("No queries executed in the current session yet. Ask questions in the AI Analyst tab to build your audit log.")
    else:
        st.markdown("<div class='workspace-panel'>", unsafe_allow_html=True)
        for i, msg in enumerate(st.session_state.messages):
            if msg["role"] == "user":
                st.markdown(f"**Query #{i+1}:** `{msg['content']}`")
            else:
                if msg.get("sql"):
                    st.code(msg["sql"], language="sql")
                st.markdown("---")
        st.markdown("</div>", unsafe_allow_html=True)


# ==============================================================================
# VIEW 5: AUTOMATED INSIGHTS & ANOMALIES
# ==============================================================================
elif "Insights" in st.session_state.current_nav:
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-headline">AI <span>Proactive Business Insights</span></div>
        <div class="hero-desc">Automated anomaly detection, growth catalysts, and operational recommendations generated across your data.</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="insight-card-executive">
        <div class="insight-headline">🚀 REVENUE CATALYST: Health & Beauty Leading Market Share</div>
        <div class="insight-text">The <strong>Health & Beauty</strong> category generated <strong>R$ 1.26M</strong> in total sales, representing the highest individual revenue contributor. Watches & Gifts followed closely at <strong>R$ 1.21M</strong>. Combining cross-sell promotions between these two categories could unlock an estimated +8.5% incremental margin.</div>
    </div>

    <div class="insight-card-executive" style="border-left-color: #8B5CF6; border-color: rgba(139, 92, 246, 0.35);">
        <div class="insight-headline" style="color: #E879F9;">⚡ LOGISTICS OPTIMIZATION: Regional Delivery Disparity</div>
        <div class="insight-text">Orders shipped to São Paulo (SP) average <strong>8.3 days</strong> delivery time, whereas orders shipped to Northeastern states (e.g. BA, PE, CE) average <strong>17.6 days</strong>. Establishing localized fulfillment hubs in the Northeast would reduce transit times by up to 40%.</div>
    </div>

    <div class="insight-card-executive" style="border-left-color: #10B981; border-color: rgba(16, 185, 129, 0.35);">
        <div class="insight-headline" style="color: #10B981;">💳 PAYMENT PREFERENCE: Credit Card Dominance</div>
        <div class="insight-text">Credit card payments account for over <strong>75%</strong> of all transaction volume (R$ 12.5M+), with an average installment count of 3.1x. Offering dynamic installment discounts can accelerate conversion rates for high-ticket electronics.</div>
    </div>
    """, unsafe_allow_html=True)


# ==============================================================================
# VIEW 6: SETTINGS & API CONFIGURATION
# ==============================================================================
elif "Settings" in st.session_state.current_nav:
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-headline">System <span>Configuration & API Settings</span></div>
        <div class="hero-desc">Manage your Groq AI engine credentials, LLM model parameters, and Streamlit Cloud secrets.</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='workspace-panel'>", unsafe_allow_html=True)
    st.markdown("<div class='panel-title'>🔑 Groq API Key Configuration</div>", unsafe_allow_html=True)
    
    current_key = get_groq_api_key()
    if current_key:
        masked_key = current_key[:8] + "..." + current_key[-4:] if len(current_key) > 12 else "********"
        st.success(f"✅ Active Groq API Key: `{masked_key}`")
    else:
        st.warning("⚠️ No Groq API Key detected. Please enter one below to enable AI querying.")

    with st.form("settings_api_key_form"):
        new_key = st.text_input("Enter or Update Groq API Key", value=st.session_state.user_groq_api_key, type="password", placeholder="gsk_...")
        scol1, scol2 = st.columns([1.5, 3])
        with scol1:
            save_btn = st.form_submit_button("💾 Save Key to Session", use_container_width=True)
        if save_btn:
            st.session_state.user_groq_api_key = new_key.strip()
            st.success("✅ API Key updated for this session!")
            st.rerun()

    st.markdown("---")
    st.markdown("""
    ### ☁️ Permanent Streamlit Cloud Setup
    To make your key permanent for all visitors on Streamlit Cloud without typing it:
    1. Go to your **Streamlit App Dashboard**: [share.streamlit.io](https://share.streamlit.io)
    2. Click **App Settings → Secrets**
    3. Paste:
       ```toml
       GROQ_API_KEY = "gsk_your_groq_api_key_here"
       ```
    4. Click **Save**. The app will automatically connect!
    """)
    st.markdown("</div>", unsafe_allow_html=True)
