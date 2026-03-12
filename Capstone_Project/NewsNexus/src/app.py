import streamlit as st
import os
import time
from datetime import datetime
from langchain_core.messages import HumanMessage

# --- Import Backend ---
from ingestion import ingest_documents
from tools import get_llm_with_tools, lookup_policy_docs, web_search_stub
from agents import app as agent_app
from memory_store import MemoryStore


# ============================================================
# PATH CONFIGURATION (DYNAMIC & PORTABLE)
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # src/
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))

DATA_PATH = os.path.join(PROJECT_ROOT, "data", "raw_pdfs")
DB_PATH = os.path.join(PROJECT_ROOT, "data", "chroma_db")

os.makedirs(DATA_PATH, exist_ok=True)
os.makedirs(DB_PATH, exist_ok=True)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="NewsNexus AI",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────
# CUSTOM CSS — modern glass-card design system
# ──────────────────────────────────────────────────────────────
st.markdown(
    r"""
<style>
/* ---------- palette variables ---------- */
:root {
    --accent:       #6366F1;
    --accent-light: #A5B4FC;
    --accent-dark:  #4338CA;
    --bg-card:      rgba(255,255,255,0.70);
    --success:      #10B981;
    --warning:      #F59E0B;
    --danger:       #EF4444;
    --text-primary: #0F172A; /* Deeper indigo-slate for better readability */
    --text-muted:   #475569; /* Darker slate for readability */
    --radius:       14px;
    --shadow:       0 4px 24px rgba(0,0,0,0.06);
}

/* ---------- global background & text ---------- */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #f8faff 0%, #f1f4ff 40%, #f9f8ff 100%);
    color: var(--text-primary) !important;
}
[data-testid="stAppViewContainer"] h1,
[data-testid="stAppViewContainer"] h2,
[data-testid="stAppViewContainer"] h3,
[data-testid="stAppViewContainer"] p,
[data-testid="stAppViewContainer"] span,
[data-testid="stAppViewContainer"] label {
    color: var(--text-primary) !important;
}

/* ---------- sidebar ---------- */
[data-testid="stSidebar"] > div:first-child {
    background: linear-gradient(180deg, #1E1B4B 0%, #312E81 100%);
}
[data-testid="stSidebar"] * {
    color: #E0E7FF !important;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #FFFFFF !important;
}
section[data-testid="stSidebar"] .stButton > button {
    background: linear-gradient(135deg, var(--accent) 0%, var(--accent-dark) 100%);
    color: #fff !important;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    padding: 0.5rem 1.2rem;
    transition: transform 0.15s, box-shadow 0.15s;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(99,102,241,0.4);
}

/* ---------- hero banner ---------- */
.hero-banner {
    background: linear-gradient(135deg, #4338CA 0%, #6366F1 50%, #818CF8 100%);
    padding: 2.2rem 2.5rem 1.6rem;
    border-radius: var(--radius);
    margin-bottom: 1.4rem;
    box-shadow: var(--shadow);
    position: relative;
    overflow: hidden;
}
.hero-banner::after {
    content: "";
    position: absolute;
    top: -40%; right: -10%;
    width: 320px; height: 320px;
    background: radial-gradient(circle, rgba(255,255,255,0.12) 0%, transparent 70%);
    border-radius: 50%;
}
.hero-title {
    font-size: 2.4rem;
    font-weight: 800;
    color: #FFFFFF;
    margin: 0;
    letter-spacing: -0.5px;
}
.hero-sub {
    font-size: 1.05rem;
    color: #C7D2FE;
    margin-top: 0.3rem;
    font-weight: 400;
}

/* ---------- glass card ---------- */
.glass-card {
    background: var(--bg-card);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255,255,255,0.50);
    border-radius: var(--radius);
    padding: 1.4rem 1.6rem;
    box-shadow: var(--shadow);
    margin-bottom: 1rem;
    transition: transform 0.18s, box-shadow 0.18s;
}
.glass-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 32px rgba(0,0,0,0.10);
}

/* ---------- metric pills ---------- */
.metric-row { display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 1rem; }
.metric-pill {
    flex: 1;
    min-width: 130px;
    background: var(--bg-card);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.50);
    border-radius: 12px;
    padding: 1rem 1.2rem;
    text-align: center;
    box-shadow: var(--shadow);
}
.metric-pill .mp-value {
    font-size: 1.75rem;
    font-weight: 700;
    color: var(--accent);
}
.metric-pill .mp-label {
    font-size: 0.82rem;
    color: var(--text-muted);
    margin-top: 0.15rem;
}

/* ---------- pipeline stepper ---------- */
.pipeline { display: flex; align-items: center; gap: 0; margin: 1.2rem 0 0.8rem; }
.step-node { display: flex; flex-direction: column; align-items: center; flex: 1; }
.step-circle {
    width: 52px; height: 52px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.4rem; font-weight: 700; color: #fff;
    box-shadow: 0 3px 12px rgba(0,0,0,0.12);
    transition: transform 0.3s;
}
.step-circle.active  { background: linear-gradient(135deg,#6366F1,#818CF8); animation: pulse-ring 1.6s infinite; }
.step-circle.done    { background: linear-gradient(135deg,#10B981,#34D399); }
.step-circle.pending { background: #CBD5E1; }
.step-label { font-size: 0.78rem; color: var(--text-muted); margin-top: 6px; font-weight: 600; }
.step-connector { flex: 0.6; height: 3px; background: #CBD5E1; border-radius: 2px; margin: 0 2px; }
.step-connector.done { background: linear-gradient(90deg,#10B981,#6366F1); }
@keyframes pulse-ring {
    0%   { box-shadow: 0 0 0 0 rgba(99,102,241,0.5); }
    70%  { box-shadow: 0 0 0 10px rgba(99,102,241,0); }
    100% { box-shadow: 0 0 0 0 rgba(99,102,241,0); }
}

/* ---------- sidebar status badge ---------- */
.sidebar-badge {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 4px 12px; border-radius: 20px;
    font-size: 0.78rem; font-weight: 600;
}
.badge-online  { background: rgba(16,185,129,0.2); color: #34D399; }
.badge-offline { background: rgba(239,68,68,0.15); color: #FCA5A5; }

/* ---------- topic input ---------- */
div[data-testid="stTextInput"] > div > div > input {
    border-radius: 10px !important;
    border: 2px solid #C7D2FE !important;
    padding: 0.65rem 1rem !important;
    font-size: 1rem !important;
    transition: border 0.2s;
}
div[data-testid="stTextInput"] > div > div > input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.15) !important;
}

/* ---------- main buttons ---------- */
div.stMainBlockContainer .stButton > button {
    background: linear-gradient(135deg, var(--accent) 0%, var(--accent-dark) 100%);
    color: #fff !important;
    border: none;
    border-radius: 10px;
    font-weight: 700;
    font-size: 1rem;
    padding: 0.65rem 2rem;
    letter-spacing: 0.3px;
    transition: transform 0.15s, box-shadow 0.15s;
}
div.stMainBlockContainer .stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(99,102,241,0.35);
}

/* ---------- approved banner ---------- */
.approved-banner {
    background: linear-gradient(135deg, #065F46 0%, #10B981 100%);
    color: #fff;
    padding: 1.4rem 2rem;
    border-radius: var(--radius);
    text-align: center;
    font-size: 1.15rem;
    font-weight: 700;
    letter-spacing: 0.3px;
    box-shadow: 0 4px 20px rgba(16,185,129,0.3);
    margin-bottom: 1rem;
}

/* ---------- export card ---------- */
.export-card {
    background: var(--bg-card);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.50);
    border-radius: var(--radius);
    padding: 1.4rem;
    text-align: center;
    box-shadow: var(--shadow);
    margin-bottom: 0.5rem;
}
.export-card .ec-icon { font-size: 2rem; margin-bottom: 0.3rem; }
.export-card .ec-title { font-weight: 700; color: var(--text-primary); }

/* ---------- review header ---------- */
.review-header {
    background: linear-gradient(135deg, #312E81, #4338CA);
    color: #fff;
    padding: 1rem 1.5rem;
    border-radius: var(--radius) var(--radius) 0 0;
    font-weight: 700;
    font-size: 1.2rem;
    margin-bottom: 0;
}

/* ---------- misc helpers ---------- */
.divider-gradient {
    height: 3px;
    background: linear-gradient(90deg, transparent, var(--accent-light), transparent);
    border: none;
    margin: 1.2rem 0;
}
.finding-card {
    background: #F1F5F9;
    border-left: 4px solid var(--accent);
    padding: 1rem 1.2rem;
    border-radius: 0 10px 10px 0;
    margin-bottom: 0.8rem;
    font-size: 0.92rem;
    color: var(--text-primary);
}
</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

defaults = {
    "messages": [],
    "research_data": [],
    "chart_data": [],
    "thread_id": f"session_{int(time.time())}",
    "current_step": "idle",
    "draft_content": "",
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# UTILITIES
# ============================================================


def wrap_for_export(raw_html, title="NewsNexus Newsletter"):
    """Wrap raw agent-generated HTML in a polished, self-contained page."""
    timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  /* ---------- Reset & base ---------- */
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Segoe UI', Inter, system-ui, -apple-system, sans-serif;
    background: linear-gradient(135deg, #f0f4ff 0%, #e8ecf8 40%, #f5f3ff 100%);
    color: #1E293B;
    line-height: 1.7;
    padding: 0;
    -webkit-font-smoothing: antialiased;
  }}

  /* ---------- Header banner ---------- */
  .nx-header {{
    background: linear-gradient(135deg, #4338CA 0%, #6366F1 50%, #818CF8 100%);
    padding: 2.5rem 3rem 2rem;
    text-align: center;
    position: relative;
    overflow: hidden;
  }}
  .nx-header::after {{
    content: '';
    position: absolute;
    top: -50%; right: -15%;
    width: 400px; height: 400px;
    background: radial-gradient(circle, rgba(255,255,255,0.10) 0%, transparent 70%);
    border-radius: 50%;
  }}
  .nx-header h1 {{
    font-size: 2.2rem;
    font-weight: 800;
    color: #FFFFFF;
    letter-spacing: -0.5px;
    margin-bottom: 0.25rem;
  }}
  .nx-header .nx-tagline {{
    color: #C7D2FE;
    font-size: 0.95rem;
    font-weight: 400;
  }}

  /* ---------- Container ---------- */
  .nx-container {{
    max-width: 860px;
    margin: -1.5rem auto 2rem;
    background: rgba(255,255,255,0.85);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255,255,255,0.50);
    border-radius: 16px;
    box-shadow: 0 8px 40px rgba(0,0,0,0.08);
    padding: 2.5rem 3rem;
    position: relative;
    z-index: 1;
  }}

  /* ---------- Content typography ---------- */
  .nx-container h1 {{ font-size: 1.8rem; font-weight: 700; color: #312E81; margin: 1.6rem 0 0.6rem; border-bottom: 3px solid #A5B4FC; padding-bottom: 0.4rem; }}
  .nx-container h2 {{ font-size: 1.45rem; font-weight: 700; color: #4338CA; margin: 1.4rem 0 0.5rem; }}
  .nx-container h3 {{ font-size: 1.15rem; font-weight: 600; color: #6366F1; margin: 1.2rem 0 0.4rem; }}
  .nx-container p  {{ margin: 0.6rem 0; }}
  .nx-container ul, .nx-container ol {{ margin: 0.6rem 0 0.6rem 1.6rem; }}
  .nx-container li {{ margin-bottom: 0.35rem; }}
  .nx-container a {{
    color: #6366F1;
    text-decoration: none;
    border-bottom: 1px solid #A5B4FC;
    transition: color 0.2s, border-color 0.2s;
  }}
  .nx-container a:hover {{ color: #4338CA; border-color: #4338CA; }}
  .nx-container blockquote {{
    border-left: 4px solid #6366F1;
    background: #F1F5F9;
    padding: 0.8rem 1.2rem;
    margin: 1rem 0;
    border-radius: 0 10px 10px 0;
    font-style: italic;
    color: #475569;
  }}
  .nx-container code {{
    background: #EEF2FF;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 0.9em;
    color: #4338CA;
  }}
  .nx-container table {{
    width: 100%;
    border-collapse: collapse;
    margin: 1rem 0;
  }}
  .nx-container th {{
    background: linear-gradient(135deg, #4338CA, #6366F1);
    color: #fff;
    padding: 0.7rem 1rem;
    text-align: left;
    font-weight: 600;
  }}
  .nx-container td {{
    padding: 0.6rem 1rem;
    border-bottom: 1px solid #E2E8F0;
  }}
  .nx-container tr:nth-child(even) td {{ background: #F8FAFC; }}
  .nx-container img {{ max-width: 100%; border-radius: 10px; margin: 1rem 0; }}
  .nx-container hr {{
    border: none;
    height: 3px;
    background: linear-gradient(90deg, transparent, #A5B4FC, transparent);
    margin: 1.5rem 0;
  }}

  /* ---------- Footer ---------- */
  .nx-footer {{
    text-align: center;
    padding: 1.5rem;
    font-size: 0.8rem;
    color: #94A3B8;
  }}
  .nx-footer a {{ color: #6366F1; text-decoration: none; }}

  /* ---------- Print tweaks ---------- */
  @media print {{
    body {{ background: #fff; }}
    .nx-header {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
    .nx-container {{ box-shadow: none; border: 1px solid #E2E8F0; }}
  }}
</style>
</head>
<body>

<div class="nx-header">
  <h1>📰 NewsNexus</h1>
  <div class="nx-tagline">Corporate Intelligence Report &mdash; {timestamp}</div>
</div>

<div class="nx-container">
{raw_html}
</div>

<div class="nx-footer">
  Generated by <a href="#">NewsNexus AI</a> &middot; Powered by Llama&nbsp;3.2 &amp; LangGraph
</div>

</body>
</html>"""


def export_as_pdf(html_content):
    from io import BytesIO
    from xhtml2pdf import pisa

    pdf_buffer = BytesIO()
    pisa_status = pisa.CreatePDF(html_content, dest=pdf_buffer)
    if pisa_status.err:
        return None
    return pdf_buffer.getvalue()


def database_exists():
    return os.path.exists(DB_PATH) and len(os.listdir(DB_PATH)) > 0


def raw_pdfs_exist():
    return os.path.exists(DATA_PATH) and any(
        f.endswith(".pdf") for f in os.listdir(DATA_PATH)
    )


def render_pipeline(researcher="pending", analyst="pending", writer="pending"):
    """Render a visual 3-step agent pipeline. Each arg: 'pending' | 'active' | 'done'."""
    icons = {"researcher": "🕵️", "analyst": "🧠", "writer": "✍️"}
    labels = {"researcher": "Researcher", "analyst": "Analyst", "writer": "Writer"}
    states = {"researcher": researcher, "analyst": analyst, "writer": writer}
    parts = []
    keys = list(states.keys())
    for i, key in enumerate(keys):
        s = states[key]
        parts.append(
            f'<div class="step-node">'
            f'<div class="step-circle {s}">{icons[key]}</div>'
            f'<div class="step-label">{labels[key]}</div></div>'
        )
        if i < len(keys) - 1:
            conn = "done" if s == "done" else ""
            parts.append(f'<div class="step-connector {conn}"></div>')
    return f'<div class="pipeline">{"".join(parts)}</div>'


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown("## 📰 NewsNexus")
    st.caption("Corporate Intelligence Agent")
    st.markdown('<hr class="divider-gradient">', unsafe_allow_html=True)

    # --- System status badges ---
    db_ready = database_exists()
    existing_pdfs = []
    if os.path.exists(DATA_PATH):
        existing_pdfs = [f for f in os.listdir(DATA_PATH) if f.endswith(".pdf")]

    badge_cls = "badge-online" if db_ready else "badge-offline"
    badge_txt = "Vector DB Active" if db_ready else "Vector DB Missing"
    st.markdown(
        f'<span class="sidebar-badge {badge_cls}">● {badge_txt}</span>',
        unsafe_allow_html=True,
    )

    mode_txt = "Hybrid (PDF + Web)" if existing_pdfs else "Web Search Only"
    st.markdown(
        f"<span style='font-size:0.8rem;opacity:0.7;'>Mode: {mode_txt}</span>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<span style='font-size:0.8rem;opacity:0.7;'>LLM: Llama 3.2 via Ollama</span>",
        unsafe_allow_html=True,
    )

    st.markdown('<hr class="divider-gradient">', unsafe_allow_html=True)

    # --- Knowledge base ---
    st.markdown("### 📂 Knowledge Base")

    if existing_pdfs:
        with st.expander(f"📄 Documents ({len(existing_pdfs)})", expanded=False):
            for pdf in existing_pdfs:
                st.markdown(f"&nbsp;&nbsp;📄&ensp;`{pdf}`")
    else:
        st.info("No documents yet — upload PDFs below.", icon="📁")

    uploaded_files = st.file_uploader(
        "Upload PDF reports",
        type="pdf",
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if uploaded_files:
        for file in uploaded_files:
            save_path = os.path.join(DATA_PATH, file.name)
            with open(save_path, "wb") as f:
                f.write(file.getbuffer())
        st.success(f"Uploaded {len(uploaded_files)} file(s)!")
        st.rerun()

    if st.button("🧠  Build / Update Index", use_container_width=True):
        if not raw_pdfs_exist():
            st.warning("Upload at least one PDF first.")
        else:
            with st.spinner("Processing documents …"):
                try:
                    pages, chunks = ingest_documents()
                    st.success(f"Done — {pages} pages → {chunks} chunks")
                except Exception as e:
                    st.error(f"Ingestion error: {e}")

    st.markdown('<hr class="divider-gradient">', unsafe_allow_html=True)
    st.caption(f"Session: `{st.session_state.thread_id[:18]}…`")


# ============================================================
# HERO BANNER
# ============================================================

st.markdown(
    """
<div class="hero-banner">
    <p class="hero-title">📰 NewsNexus</p>
    <p class="hero-sub">Autonomous Multi-Agent Research &amp; Intelligence System</p>
</div>
""",
    unsafe_allow_html=True,
)


# ============================================================
# METRICS ROW
# ============================================================

mcol1, mcol2, mcol3, mcol4 = st.columns(4)
with mcol1:
    st.markdown(
        f'<div class="metric-pill"><div class="mp-value">{len(existing_pdfs)}</div>'
        f'<div class="mp-label">Documents</div></div>',
        unsafe_allow_html=True,
    )
with mcol2:
    idx_icon = "✔" if db_ready else "—"
    st.markdown(
        f'<div class="metric-pill"><div class="mp-value">{idx_icon}</div>'
        f'<div class="mp-label">Vector Index</div></div>',
        unsafe_allow_html=True,
    )
with mcol3:
    st.markdown(
        '<div class="metric-pill"><div class="mp-value">3</div>'
        '<div class="mp-label">AI Agents</div></div>',
        unsafe_allow_html=True,
    )
with mcol4:
    sources = 1 + (1 if existing_pdfs else 0) + 1  # web + pdf? + rss
    st.markdown(
        f'<div class="metric-pill"><div class="mp-value">{sources}</div>'
        f'<div class="mp-label">Data Sources</div></div>',
        unsafe_allow_html=True,
    )


# ============================================================
# TOPIC INPUT
# ============================================================

st.markdown("### 🔍 Research a Topic")
topic = st.text_input(
    "Enter your research query below:",
    placeholder="e.g., Impact of Generative AI on the Banking Sector in 2025",
    label_visibility="collapsed",
)

# ============================================================
# START AGENTS
# ============================================================

if (
    st.button(
        "🚀  Launch Agents",
        disabled=st.session_state.current_step != "idle",
        use_container_width=True,
    )
    and topic
):

    if database_exists():
        st.success("📂 Using existing Knowledge Base …")
    elif raw_pdfs_exist():
        with st.spinner("🔍 Indexing PDFs for the first time …"):
            try:
                pages, chunks = ingest_documents()
                st.success(f"Library indexed — {pages} pages, {chunks} chunks")
            except Exception as e:
                st.error(f"Auto-index failed: {e}")
                st.stop()
    else:
        st.warning("🌐 No PDFs found. Web search mode only.")

    st.session_state.current_step = "researching"
    st.session_state.messages = [HumanMessage(content=topic)]
    st.session_state.research_data = []

    try:
        mem_store = MemoryStore()
        with st.spinner("Checking historical archives …"):
            past_memory = mem_store.check_memory(topic)
        if "WARNING" in past_memory:
            st.warning(past_memory)
    except Exception as e:
        st.error(f"Memory error: {e}")
        st.stop()


# ============================================================
# AGENT EXECUTION — live pipeline
# ============================================================

if st.session_state.current_step == "researching":

    # Pipeline visualisation
    st.markdown(render_pipeline("active", "pending", "pending"), unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        research_status = st.status("🕵️ Researcher Agent", expanded=True)
    with col2:
        analyst_status = st.status("🧠 Analyst Agent", state="running", expanded=False)
    with col3:
        writer_status = st.status("✍️ Writer Agent", state="running", expanded=False)

    config = {"configurable": {"thread_id": st.session_state.thread_id}}
    inputs = {
        "messages": st.session_state.messages,
        "research_data": [],
        "chart_data": [],
    }

    try:
        for event in agent_app.stream(inputs, config):

            if "Researcher" in event:
                data = event["Researcher"]
                st.session_state.research_data = data.get("research_data", [])
                with research_status:
                    for item in st.session_state.research_data:
                        st.markdown(f"---\n{item}")
                research_status.update(
                    label=f"Researcher — {len(st.session_state.research_data)} items found",
                    state="complete",
                    expanded=False,
                )
                analyst_status.update(expanded=True)

            if "Analyst" in event:
                data = event["Analyst"]
                st.session_state.chart_data = data.get("chart_data", [])
                with analyst_status:
                    st.write("Identified trends & extracted data:")
                    if st.session_state.chart_data:
                        st.json(st.session_state.chart_data)
                    else:
                        st.write("No numeric trends found.")
                analyst_status.update(
                    label="Analyst — Complete", state="complete", expanded=False
                )
                writer_status.update(expanded=True)

            if "Writer" in event:
                data = event["Writer"]
                st.session_state.draft_content = data["messages"][-1].content
                with writer_status:
                    st.success("Draft generated!")
                    st.code(st.session_state.draft_content[:200] + "…", language="html")
                writer_status.update(label="Writer — Complete", state="complete")

        st.session_state.current_step = "reviewing"
        st.rerun()

    except Exception as e:
        st.error(f"Execution error: {e}")


# ============================================================
# REVIEW STAGE — Human-in-the-Loop
# ============================================================

if st.session_state.current_step == "reviewing":

    # Pipeline shows all done
    st.markdown(render_pipeline("done", "done", "done"), unsafe_allow_html=True)
    st.markdown(
        '<div class="review-header">📝 Draft Review — Human-in-the-Loop</div>',
        unsafe_allow_html=True,
    )

    # Chart visualisation
    if st.session_state.chart_data:
        import plotly.express as px
        import pandas as pd

        st.markdown("#### 📊 Extracted Trend Analysis")
        df = pd.DataFrame(st.session_state.chart_data)
        fig = px.bar(
            df,
            x="label",
            y="value",
            title="Data Visualization",
            color="label",
            color_discrete_sequence=px.colors.qualitative.Prism,
            template="plotly_white",
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif"),
            margin=dict(t=50, b=30),
        )
        st.plotly_chart(fig, use_container_width=True)

    # Tabbed views
    tab1, tab2 = st.tabs(["📄 Newsletter Draft", "🔍 Raw Research Log"])

    with tab1:
        st.components.v1.html(
            wrap_for_export(st.session_state.draft_content), height=600, scrolling=True
        )

    with tab2:
        st.markdown("### 🕵️ Raw Research Findings")
        if st.session_state.research_data:
            for i, data in enumerate(st.session_state.research_data):
                st.markdown(
                    f'<div class="finding-card"><strong>Finding {i + 1}</strong><br>{data}</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.warning(
                "No raw research data. Agents may have relied on internal knowledge."
            )

    st.markdown('<hr class="divider-gradient">', unsafe_allow_html=True)

    # Feedback area
    fcol1, fcol2 = st.columns([4, 1])
    with fcol1:
        feedback = st.text_input(
            "Feedback",
            placeholder="Leave empty to approve, or type revision notes …",
            label_visibility="collapsed",
        )
    with fcol2:
        submit = st.button("✅  Submit", use_container_width=True)

    if submit:
        config = {"configurable": {"thread_id": st.session_state.thread_id}}

        if feedback:
            agent_app.update_state(
                config, {"messages": [HumanMessage(content=feedback)]}
            )
            for _ in agent_app.stream(None, config):
                pass
            state = agent_app.get_state(config)
            st.session_state.draft_content = state.values["messages"][-1].content
            st.session_state.chart_data = state.values.get("chart_data", [])
            st.rerun()
        else:
            st.session_state.current_step = "finished"
            mem_store = MemoryStore()
            topic_key = st.session_state.messages[0].content
            mem_store.save_memory(topic_key, st.session_state.draft_content)
            st.rerun()


# ============================================================
# FINAL STAGE
# ============================================================

if st.session_state.current_step == "finished":

    st.balloons()
    st.markdown(
        '<div class="approved-banner">✅ Newsletter Approved &amp; Archived Successfully</div>',
        unsafe_allow_html=True,
    )

    # Build the polished export HTML once
    styled_html = wrap_for_export(st.session_state.draft_content)
    styled_pdf = export_as_pdf(styled_html)

    # Export cards
    ecol1, ecol2, ecol3 = st.columns(3)

    with ecol1:
        st.markdown(
            '<div class="export-card"><div class="ec-icon">📄</div>'
            '<div class="ec-title">HTML Export</div></div>',
            unsafe_allow_html=True,
        )
        st.download_button(
            label="⬇  Download HTML",
            data=styled_html,
            file_name=f"newsletter_{int(time.time())}.html",
            mime="text/html",
            use_container_width=True,
        )

    with ecol2:
        st.markdown(
            '<div class="export-card"><div class="ec-icon">📁</div>'
            '<div class="ec-title">PDF Export</div></div>',
            unsafe_allow_html=True,
        )
        if styled_pdf:
            st.download_button(
                label="⬇  Download PDF",
                data=styled_pdf,
                file_name=f"newsletter_{int(time.time())}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        else:
            st.error("PDF export failed.")

    with ecol3:
        st.markdown(
            '<div class="export-card"><div class="ec-icon">🔄</div>'
            '<div class="ec-title">New Research</div></div>',
            unsafe_allow_html=True,
        )
        if st.button("🔄  Start Over", use_container_width=True):
            st.session_state.current_step = "idle"
            st.rerun()

    st.markdown('<hr class="divider-gradient">', unsafe_allow_html=True)
    st.markdown("### 📰 Final Output Preview")
    st.components.v1.html(styled_html, height=800, scrolling=True)
