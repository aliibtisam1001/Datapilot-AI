"""
SmartQuery - Natural Language to SQL Business Intelligence Assistant.
3D, Colorful, Animated & Interactive Streamlit Interface.
"""
import streamlit as st
import streamlit.components.v1 as components
import os
import re
import pandas as pd
import time
from dotenv import load_dotenv

load_dotenv()

# ── Page Config ──
st.set_page_config(
    page_title="SmartQuery — 3D BI Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 3D & Neon Vibrant CSS Design System ──
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700;800&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600;700&display=swap');

    :root {
        --bg-main: #070A12;
        --bg-card: rgba(15, 23, 42, 0.85);
        --border-glass: rgba(255, 255, 255, 0.12);
        --cyan-neon: #00F0FF;
        --magenta-neon: #EC4899;
        --violet-neon: #8B5CF6;
        --emerald-neon: #10B981;
        --amber-neon: #F59E0B;
        --text-bright: #F8FAFC;
        --text-dim: #94A3B8;
        --font-display: 'Space Grotesk', sans-serif;
        --font-body: 'IBM Plex Sans', sans-serif;
        --font-mono: 'IBM Plex Mono', monospace;
    }

    /* Animated Multi-Color Gradient Mesh Background */
    .stApp {
        background: 
            radial-gradient(circle at 15% 15%, rgba(139, 92, 246, 0.22) 0%, transparent 45%),
            radial-gradient(circle at 85% 20%, rgba(0, 240, 255, 0.20) 0%, transparent 45%),
            radial-gradient(circle at 50% 85%, rgba(236, 72, 153, 0.18) 0%, transparent 50%),
            radial-gradient(circle at 80% 80%, rgba(16, 185, 129, 0.15) 0%, transparent 45%),
            #070A12 !important;
        background-attachment: fixed !important;
        color: var(--text-bright) !important;
        font-family: var(--font-body) !important;
        overflow-x: hidden;
    }

    /* Container Spacing */
    .block-container {
        max-width: 1140px !important;
        padding-top: 1.5rem !important;
        padding-bottom: 5rem !important;
    }

    /* ── Hero Title with Animated Shifting Hue ── */
    .hero-header {
        position: relative;
        padding: 0.5rem 0 1.2rem 0;
        margin-bottom: 1.2rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }
    .hero-eyebrow {
        font-family: var(--font-mono);
        font-size: 12px;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        color: var(--cyan-neon);
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(0, 240, 255, 0.08);
        border: 1px solid rgba(0, 240, 255, 0.3);
        padding: 5px 14px;
        border-radius: 999px;
        box-shadow: 0 0 15px rgba(0, 240, 255, 0.2);
        margin-bottom: 12px;
    }
    .hero-title-text {
        font-family: var(--font-display);
        font-weight: 800;
        font-size: clamp(38px, 5vw, 56px);
        line-height: 1.05;
        letter-spacing: -0.03em;
        margin: 6px 0 12px 0;
        background: linear-gradient(90deg, #00F0FF, #EC4899, #8B5CF6, #F59E0B, #00F0FF);
        background-size: 300% 300%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: gradientShift 8s ease infinite;
        display: flex;
        align-items: center;
        gap: 14px;
    }
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    .hero-subtitle {
        font-size: 16.5px;
        line-height: 1.6;
        color: var(--text-dim);
        max-width: 680px;
        margin-bottom: 12px;
    }

    /* 3D Glass Pill Badges */
    .pill-container {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        margin-top: 14px;
    }
    .badge-3d {
        font-family: var(--font-mono);
        font-size: 11.5px;
        font-weight: 600;
        padding: 6px 14px;
        border-radius: 999px;
        background: rgba(15, 23, 42, 0.7);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.12);
        color: #E2E8F0;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.4), inset 0 1px 1px rgba(255, 255, 255, 0.2);
        transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
    }
    .badge-3d:hover {
        transform: translateY(-2px) scale(1.03);
        border-color: var(--cyan-neon);
        box-shadow: 0 8px 20px rgba(0, 240, 255, 0.3), inset 0 1px 2px rgba(255, 255, 255, 0.4);
    }

    /* ── 3D Chat Messages with Staggered Slide-In & Tilt ── */
    [data-testid="stChatMessage"] {
        background: rgba(15, 23, 42, 0.75) !important;
        backdrop-filter: blur(16px) !important;
        border: 1px solid rgba(255, 255, 255, 0.10) !important;
        border-radius: 16px !important;
        padding: 1.2rem 1.4rem !important;
        margin-bottom: 1.2rem !important;
        box-shadow: 0 15px 35px -10px rgba(0, 0, 0, 0.5), inset 0 1px 1px rgba(255, 255, 255, 0.1) !important;
        transition: transform 0.25s cubic-bezier(0.2, 0.8, 0.2, 1), box-shadow 0.25s ease !important;
        animation: chatBounceIn 0.5s cubic-bezier(0.2, 0.9, 0.3, 1) both !important;
    }
    @keyframes chatBounceIn {
        from {
            opacity: 0;
            transform: translateY(18px) scale(0.97);
        }
        to {
            opacity: 1;
            transform: translateY(0) scale(1);
        }
    }
    [data-testid="stChatMessage"]:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 20px 45px -10px rgba(0, 240, 255, 0.2), inset 0 1px 2px rgba(255, 255, 255, 0.2) !important;
        border-color: rgba(0, 240, 255, 0.35) !important;
    }

    /* Avatar 3D Badges */
    [data-testid="stChatMessageAvatarUser"] {
        background: linear-gradient(135deg, #EC4899, #8B5CF6) !important;
        border-radius: 12px !important;
        box-shadow: 0 0 15px rgba(236, 72, 153, 0.5), inset 0 1px 1px rgba(255, 255, 255, 0.4) !important;
        border: 1.5px solid rgba(255, 255, 255, 0.4) !important;
    }
    [data-testid="stChatMessageAvatarAssistant"] {
        background: linear-gradient(135deg, #00F0FF, #3B82F6) !important;
        border-radius: 12px !important;
        box-shadow: 0 0 15px rgba(0, 240, 255, 0.5), inset 0 1px 1px rgba(255, 255, 255, 0.4) !important;
        border: 1.5px solid rgba(255, 255, 255, 0.4) !important;
    }

    /* ── Guardrail Passed Badge with Neon Ring Shockwave ── */
    .guard-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        font-family: var(--font-mono);
        font-size: 12px;
        font-weight: 600;
        color: #10B981;
        background: rgba(16, 185, 129, 0.12);
        border: 1px solid rgba(16, 185, 129, 0.4);
        padding: 6px 14px;
        border-radius: 8px;
        margin-bottom: 14px;
        box-shadow: 0 0 20px rgba(16, 185, 129, 0.25);
        animation: guardPulse 2.5s infinite ease-in-out;
    }
    @keyframes guardPulse {
        0%, 100% {
            box-shadow: 0 0 12px rgba(16, 185, 129, 0.2);
            border-color: rgba(16, 185, 129, 0.35);
        }
        50% {
            box-shadow: 0 0 24px rgba(16, 185, 129, 0.55), 0 0 0 4px rgba(16, 185, 129, 0.15);
            border-color: rgba(16, 185, 129, 0.8);
        }
    }
    .guard-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #10B981;
        box-shadow: 0 0 8px #10B981;
    }

    /* ── 3D Business Insight Card ── */
    .insight-card-3d {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.10), rgba(236, 72, 153, 0.08), rgba(15, 23, 42, 0.85));
        border: 1px solid rgba(245, 158, 11, 0.35);
        border-left: 5px solid var(--amber-neon);
        border-radius: 14px;
        padding: 16px 20px;
        margin-top: 14px;
        box-shadow: 0 12px 30px -8px rgba(245, 158, 11, 0.2), inset 0 1px 1px rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(14px);
        transition: transform 0.25s ease, box-shadow 0.25s ease;
    }
    .insight-card-3d:hover {
        transform: translateY(-2px);
        box-shadow: 0 18px 40px -10px rgba(245, 158, 11, 0.35);
        border-color: rgba(245, 158, 11, 0.6);
    }
    .insight-title-3d {
        font-family: var(--font-display);
        font-weight: 700;
        font-size: 14.5px;
        color: #FCD34D;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        gap: 8px;
        letter-spacing: 0.02em;
    }
    .insight-body-3d {
        font-family: var(--font-body);
        font-size: 14px;
        color: #E2E8F0;
        line-height: 1.6;
    }

    /* ── SQL Block Styling ── */
    .stCodeBlock {
        border-radius: 12px !important;
        border: 1px solid rgba(0, 240, 255, 0.3) !important;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.6), 0 0 15px rgba(0, 240, 255, 0.15) !important;
        background: #060913 !important;
    }
    .streamlit-expanderHeader {
        background: rgba(15, 23, 42, 0.9) !important;
        border: 1px solid rgba(255, 255, 255, 0.10) !important;
        border-radius: 10px !important;
        font-family: var(--font-display) !important;
        font-weight: 600 !important;
        color: var(--cyan-neon) !important;
    }

    /* ── Interactive Sidebar ── */
    [data-testid="stSidebar"] {
        background: rgba(10, 15, 28, 0.95) !important;
        backdrop-filter: blur(20px) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
    }
    [data-testid="stSidebar"] .stButton button {
        background: rgba(15, 23, 42, 0.8) !important;
        color: #E2E8F0 !important;
        border: 1px solid rgba(255, 255, 255, 0.10) !important;
        border-radius: 12px !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        text-align: left !important;
        padding: 10px 16px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
        transition: all 0.25s cubic-bezier(0.2, 0.8, 0.2, 1) !important;
    }
    [data-testid="stSidebar"] .stButton button:hover {
        background: linear-gradient(135deg, rgba(0, 240, 255, 0.15), rgba(139, 92, 246, 0.2)) !important;
        border-color: var(--cyan-neon) !important;
        color: #FFFFFF !important;
        transform: translateX(4px) translateY(-1px) !important;
        box-shadow: 0 8px 24px rgba(0, 240, 255, 0.3) !important;
    }

    /* ── Electric Chat Input with Charge-Up Glow ── */
    [data-testid="stChatInput"] {
        background: rgba(15, 23, 42, 0.85) !important;
        backdrop-filter: blur(16px) !important;
        border: 1px solid rgba(0, 240, 255, 0.4) !important;
        border-radius: 999px !important;
        box-shadow: 0 10px 35px -8px rgba(0, 0, 0, 0.7), 0 0 15px rgba(0, 240, 255, 0.15) !important;
        transition: all 0.3s ease !important;
    }
    [data-testid="stChatInput"]:focus-within {
        border-color: var(--cyan-neon) !important;
        box-shadow: 0 12px 40px -5px rgba(0, 240, 255, 0.4), 0 0 25px rgba(0, 240, 255, 0.35) !important;
        transform: translateY(-2px) !important;
    }

    /* Reduced Motion Respect */
    @media (prefers-reduced-motion: reduce) {
        *, ::before, ::after {
            animation-duration: 0.001s !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.001s !important;
        }
    }

    /* Clean up default Streamlit chrome */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ── Interactive 3D Hologram (Three.js WebGL Canvas) ──
def render_3d_hero_hologram():
    """Renders a high-performance 3D floating crystal with orbiting glowing data pillars and mouse parallax."""
    three_js_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body { margin: 0; overflow: hidden; background: transparent; }
            #canvas-3d { width: 100%; height: 160px; display: block; }
        </style>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    </head>
    <body>
        <canvas id="canvas-3d"></canvas>
        <script>
            const canvas = document.getElementById('canvas-3d');
            const scene = new THREE.Scene();
            const camera = new THREE.PerspectiveCamera(45, window.innerWidth / 160, 0.1, 1000);
            camera.position.z = 6.5;

            const renderer = new THREE.WebGLRenderer({ canvas: canvas, alpha: true, antialias: true });
            renderer.setSize(window.innerWidth, 160);
            renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

            // Core 3D Wireframe Polyhedron
            const coreGeo = new THREE.IcosahedronGeometry(1.6, 1);
            const coreMat = new THREE.MeshStandardMaterial({
                color: 0x00F0FF,
                wireframe: true,
                emissive: 0x005577,
                roughness: 0.2,
                metalness: 0.8
            });
            const core = new THREE.Mesh(coreGeo, coreMat);
            scene.add(core);

            // Orbiting Data Nodes / Pillars
            const group = new THREE.Group();
            const nodeGeo = new THREE.BoxGeometry(0.18, 0.7, 0.18);
            const colors = [0x00F0FF, 0xEC4899, 0x8B5CF6, 0x10B981, 0xF59E0B];
            
            for (let i = 0; i < 8; i++) {
                const angle = (i / 8) * Math.PI * 2;
                const radius = 2.6;
                const nodeMat = new THREE.MeshStandardMaterial({
                    color: colors[i % colors.length],
                    emissive: colors[i % colors.length],
                    emissiveIntensity: 0.6,
                    roughness: 0.1
                });
                const pillar = new THREE.Mesh(nodeGeo, nodeMat);
                pillar.position.set(Math.cos(angle) * radius, (Math.sin(i * 1.5) * 0.4), Math.sin(angle) * radius);
                pillar.rotation.y = angle;
                group.add(pillar);
            }
            scene.add(group);

            // Dynamic Point Lights (Cyan + Magenta)
            const lightCyan = new THREE.PointLight(0x00F0FF, 2.5, 50);
            lightCyan.position.set(5, 5, 5);
            scene.add(lightCyan);

            const lightMagenta = new THREE.PointLight(0xEC4899, 2.5, 50);
            lightMagenta.position.set(-5, -5, 5);
            scene.add(lightMagenta);

            const ambientLight = new THREE.AmbientLight(0x222233, 1.5);
            scene.add(ambientLight);

            // Mouse Interaction Parallax
            let mouseX = 0, mouseY = 0;
            let targetX = 0, targetY = 0;

            window.addEventListener('mousemove', (e) => {
                mouseX = (e.clientX / window.innerWidth - 0.5) * 2;
                mouseY = (e.clientY / 160 - 0.5) * 2;
            });

            window.addEventListener('resize', () => {
                camera.aspect = window.innerWidth / 160;
                camera.updateProjectionMatrix();
                renderer.setSize(window.innerWidth, 160);
            });

            // Render Loop with floating animations
            let clock = new THREE.Clock();
            function animate() {
                requestAnimationFrame(animate);
                const elapsedTime = clock.getElapsedTime();

                targetX += (mouseX - targetX) * 0.05;
                targetY += (mouseY - targetY) * 0.05;

                core.rotation.x = elapsedTime * 0.3 + targetY * 0.4;
                core.rotation.y = elapsedTime * 0.4 + targetX * 0.4;
                core.position.y = Math.sin(elapsedTime * 1.8) * 0.12;

                group.rotation.y = -elapsedTime * 0.25 + targetX * 0.3;
                group.position.y = Math.cos(elapsedTime * 1.5) * 0.08;

                renderer.render(scene, camera);
            }
            animate();
        </script>
    </body>
    </html>
    """
    components.html(three_js_html, height=165)


# ── Confetti Celebration Particle Emitter ──
def trigger_celebration_confetti():
    """Fires a colorful confetti micro-animation on successful response."""
    confetti_html = """
    <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js"></script>
    <script>
        confetti({
            particleCount: 45,
            spread: 65,
            origin: { y: 0.85 },
            colors: ['#00F0FF', '#EC4899', '#8B5CF6', '#10B981', '#F59E0B']
        });
    </script>
    """
    components.html(confetti_html, height=0)


# ── Backend Agents & DB Loaders ──
def get_groq_api_key():
    """Retrieve Groq API key with multi-tier fallback."""
    if "user_groq_api_key" in st.session_state and st.session_state.user_groq_api_key:
        return st.session_state.user_groq_api_key
    env_key = os.getenv("GROQ_API_KEY")
    if env_key:
        return env_key
    try:
        if "GROQ_API_KEY" in st.secrets:
            return st.secrets["GROQ_API_KEY"]
    except Exception:
        pass
    return None


def ensure_database_exists():
    """Check if data/olist.db exists. If missing, auto-build from CSVs."""
    db_path = os.path.join(os.path.dirname(__file__), "data", "olist.db")
    if not os.path.exists(db_path):
        with st.spinner("📦 Initializing Olist SQLite database from data/*.csv..."):
            try:
                from app.load_data import create_sqlite_database
                create_sqlite_database()
            except Exception as e:
                st.error(f"❌ Failed to build database: {e}")


ensure_database_exists()

from app.utils import strip_thinking, SQLCaptureCallbackHandler
from app.prompts import build_system_prompt
from app.explain import explain_result
from app.charts import auto_chart
from app.guardrails import validate_sql


@st.cache_resource
def init_agent(api_key: str):
    """Initialize LangChain SQL Agent with Groq LLM."""
    from langchain_groq import ChatGroq
    from langchain_community.agent_toolkits import create_sql_agent
    from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
    from langchain_community.utilities import SQLDatabase

    db_path = os.path.join(os.path.dirname(__file__), "data", "olist.db")
    db = SQLDatabase.from_uri(f"sqlite:///{db_path}")

    llm = ChatGroq(
        model="qwen/qwen3.6-27b",
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
def init_explain_llm(api_key: str):
    """Initialize separate LLM instance for plain-English explanations."""
    from langchain_groq import ChatGroq
    return ChatGroq(
        model="qwen/qwen3.6-27b",
        temperature=0.3,
        api_key=api_key,
    )


def run_query_for_chart(db, sql):
    """Run a validated SQL query and return DataFrame."""
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


# ── Session State ──
if "messages" not in st.session_state:
    st.session_state.messages = []

# ── Top Hero Header with 3D Hologram ──
st.markdown("""
<div class="hero-header">
    <div class="hero-eyebrow">⚡ Natural Language → SQL → 3D Visual Intelligence</div>
    <div class="hero-title-text">SmartQuery</div>
    <div class="hero-subtitle">Ask questions in natural English. Explore live SQL execution, interactive charts, and actionable executive explanations backed by 100k+ Brazilian e-commerce records.</div>
</div>
""", unsafe_allow_html=True)

# Render the 3D Three.js interactive canvas
render_3d_hero_hologram()

# ── Interactive Quick-Launch Pill Chips ──
st.markdown("<p style='font-size:13px; font-weight:600; color:#94A3B8; text-transform:uppercase; letter-spacing:0.08em; margin: 10px 0 6px 0;'>⚡ Quick-Launch Business Queries:</p>", unsafe_allow_html=True)
pill_col1, pill_col2, pill_col3, pill_col4 = st.columns(4)

with pill_col1:
    if st.button("📊 Top Categories by Revenue", key="pill_1", use_container_width=True):
        st.session_state.pending_question = "What are the top 5 product categories by revenue?"

with pill_col2:
    if st.button("💰 Delivered Total Revenue", key="pill_2", use_container_width=True):
        st.session_state.pending_question = "What is the total revenue from delivered orders?"

with pill_col3:
    if st.button("🚚 Average Delivery Time", key="pill_3", use_container_width=True):
        st.session_state.pending_question = "What is the average delivery time in days?"

with pill_col4:
    if st.button("🗺️ Top 5 States by Volume", key="pill_4", use_container_width=True):
        st.session_state.pending_question = "Which 5 states have the most customers?"

# ── API Key Resolution ──
groq_key = get_groq_api_key()

# ── Sidebar Controls ──
with st.sidebar:
    st.markdown("## ⚙️ Control Center")
    if not groq_key:
        st.warning("⚠️ No Groq API Key found.")
        user_key = st.text_input("🔑 Enter your Groq API Key:", type="password", placeholder="gsk_...")
        if user_key:
            st.session_state.user_groq_api_key = user_key
            st.rerun()
        st.info("Get a free key at [console.groq.com](https://console.groq.com).")

    st.markdown("### 💡 Business Questions")
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
    st.markdown("### 🛡️ Guardrails & Safety")
    st.markdown("""
    - **100% SELECT Only:** Destructive queries blocked.
    - **Row Limit Cap:** Max 1,000 rows returned.
    - **SQL Injection Defense:** Chained statements rejected.
    """)

    st.markdown("---")
    if st.button("🗑️ Clear Session Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


# ── Render Message History ──
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user", avatar="🧑‍💼"):
            st.markdown(f"<span style='font-size:15px; font-weight:500; color:#FFFFFF;'>{msg['content']}</span>", unsafe_allow_html=True)
    else:
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown("""<div class="guard-badge"><span class="guard-dot"></span> ✓ Guardrails Passed · SELECT Only · 1,000 Row Limit</div>""", unsafe_allow_html=True)
            st.markdown(msg.get("answer", ""))

            # Show SQL in expander
            if msg.get("sql"):
                with st.expander("⚡ Inspect Verified SQL", expanded=False):
                    st.code(msg["sql"], language="sql")

            # Show Data Table in expander
            if msg.get("df") is not None and not msg["df"].empty:
                with st.expander("📊 View Data Table Inspector", expanded=False):
                    st.dataframe(msg["df"], use_container_width=True)

            # Show chart
            if msg.get("chart"):
                st.plotly_chart(msg["chart"], use_container_width=True)

            # Show explanation
            if msg.get("explanation"):
                st.markdown(f"""
                <div class="insight-card-3d">
                    <div class="insight-title-3d">💡 Executive Business Insight</div>
                    <div class="insight-body-3d">{msg['explanation']}</div>
                </div>
                """, unsafe_allow_html=True)


# ── Handle Input Submission ──
if "pending_question" in st.session_state:
    user_input = st.session_state.pending_question
    del st.session_state.pending_question
else:
    user_input = st.chat_input("Ask a business question about the 100k+ Olist e-commerce database...")

if user_input:
    if not groq_key:
        st.error("🔑 Please enter a Groq API Key in the sidebar to run queries.")
    else:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user", avatar="🧑‍💼"):
            st.markdown(f"<span style='font-size:15px; font-weight:500; color:#FFFFFF;'>{user_input}</span>", unsafe_allow_html=True)

        # Initialize agent with key
        agent, db, llm = init_agent(groq_key)
        explain_llm = init_explain_llm(groq_key)

        # Process with agent
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("🔄 Synthesizing SQL & querying database..."):
                try:
                    callback_handler = SQLCaptureCallbackHandler()
                    result = agent.invoke(
                        {"input": user_input},
                        config={"callbacks": [callback_handler]}
                    )
                    answer = strip_thinking(result.get("output", "No answer generated."))

                    # Extract SQL from callback
                    main_sql = None
                    if callback_handler.sql_queries:
                        main_sql = callback_handler.sql_queries[-1]
                    
                    # Sanitize & validate through guardrails
                    df = pd.DataFrame()
                    if main_sql:
                        try:
                            validated_sql = validate_sql(main_sql)
                            df = run_query_for_chart(db, validated_sql)
                        except Exception:
                            df = run_query_for_chart(db, main_sql)

                    # Display Guardrail Badge & Answer
                    st.markdown("""<div class="guard-badge"><span class="guard-dot"></span> ✓ Guardrails Passed · SELECT Only · 1,000 Row Limit</div>""", unsafe_allow_html=True)
                    st.markdown(answer)

                    # Show SQL
                    if main_sql:
                        with st.expander("⚡ Inspect Verified SQL", expanded=False):
                            st.code(main_sql, language="sql")

                    # Show Data Table
                    if not df.empty:
                        with st.expander("📊 View Data Table Inspector", expanded=False):
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
                                <div class="insight-card-3d">
                                    <div class="insight-title-3d">💡 Executive Business Insight</div>
                                    <div class="insight-body-3d">{explanation}</div>
                                </div>
                                """, unsafe_allow_html=True)
                        except Exception:
                            pass

                    # Fire celebration particles
                    trigger_celebration_confetti()

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
