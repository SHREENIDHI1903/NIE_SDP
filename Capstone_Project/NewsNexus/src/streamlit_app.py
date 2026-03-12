import streamlit as st
import os
import time
import sys

# --- GLOBAL ERROR CATCHER ---
# This prevents the app from disconnecting silently on import errors
try:
    from ingestion import ingest_documents
    # We defer other imports to inside the app to prevent startup crashes
except Exception as e:
    st.error(f"CRITICAL STARTUP ERROR: {e}")
    st.stop()

# --- Configuration ---
PROJECT_ROOT = r"D:\NIE_GENai\Capstone_Project\NewsNexus"
DATA_PATH = os.path.join(PROJECT_ROOT, "data", "raw_pdfs")
DB_PATH = os.path.join(PROJECT_ROOT, "data", "chroma_db")

# --- Page Setup ---
st.set_page_config(page_title="NewsNexus AI", page_icon="📰", layout="wide")

# --- Styles ---
st.markdown("""
<style>
    .main-header {font-size: 2.5rem; color: #1E3A8A; font-weight: bold;}
    .agent-box {border: 1px solid #ddd; padding: 15px; border-radius: 10px; margin-bottom: 10px; background-color: #f9f9f9;}
</style>
""", unsafe_allow_html=True)

# --- State Initialization ---
if "messages" not in st.session_state: st.session_state.messages = []
if "research_data" not in st.session_state: st.session_state.research_data = []
if "chart_data" not in st.session_state: st.session_state.chart_data = []
if "draft_content" not in st.session_state: st.session_state.draft_content = ""
if "current_step" not in st.session_state: st.session_state.current_step = "idle" 
if "thread_id" not in st.session_state: st.session_state.thread_id = f"session_{int(time.time())}"
if "topic" not in st.session_state: st.session_state.topic = ""

# --- Helper Functions ---
def export_as_pdf(html_content):
    try:
        from io import BytesIO
        from xhtml2pdf import pisa
        pdf_buffer = BytesIO()
        pisa_status = pisa.CreatePDF(html_content, dest=pdf_buffer)
        if pisa_status.err: return None
        return pdf_buffer.getvalue()
    except:
        return None

# --- Sidebar ---
with st.sidebar:
    st.title("NewsNexus Control")
    st.subheader("📂 Knowledge Base")
    
    # File Uploader
    uploaded_files = st.file_uploader("Add PDFs", type="pdf", accept_multiple_files=True)
    if uploaded_files:
        os.makedirs(DATA_PATH, exist_ok=True)
        for uploaded_file in uploaded_files:
            save_path = os.path.join(DATA_PATH, uploaded_file.name)
            with open(save_path, "wb") as f: f.write(uploaded_file.getbuffer())
        st.success(f"Uploaded {len(uploaded_files)} files.")
        
    # Process Button (Synchronous - Freezes UI until done, but safe)
    if st.button("🧠 Process PDFs (Blocking)"):
        with st.spinner("Processing... Do not close the tab."):
            try:
                # Run directly without threading
                pages, chunks = ingest_documents()
                st.success(f"Done! Processed {pages} pages into {chunks} chunks.")
            except Exception as e:
                st.error(f"Ingestion Failed: {e}")

    # Status
    db_exists = os.path.exists(DB_PATH) and os.listdir(DB_PATH)
    st.info(f"Database: {'✅ Active' if db_exists else '⚠️ Empty'}")

# --- Main App ---
st.markdown('<div class="main-header">📰 NewsNexus Agent</div>', unsafe_allow_html=True)
topic_input = st.text_input("Enter Topic:", placeholder="e.g. AI trends in 2024")

# Start Button
if st.button("🚀 Start Agents", disabled=st.session_state.current_step != "idle") and topic_input:
    st.session_state.topic = topic_input
    st.session_state.current_step = "researching"
    st.rerun()

# --- LOGIC: RESEARCHING ---
if st.session_state.current_step == "researching":
    st.info("Agents are running... Please wait.")
    
    # UI Layout
    col1, col2, col3 = st.columns(3)
    r_container = col1.container(border=True)
    a_container = col2.container(border=True)
    w_container = col3.container(border=True)
    
    r_container.write("🕵️ **Researcher**")
    a_container.write("🧠 **Analyst**")
    w_container.write("✍️ **Writer**")

    # EXECUTION
    try:
        # Import inside try/catch to identify crash location
        from agents import app as agent_app
        from langchain_core.messages import HumanMessage
        from memory_store import MemoryStore

        # Memory Check
        try:
            mem = MemoryStore()
            check = mem.check_memory(st.session_state.topic)
            if "WARNING" in check: st.warning(check)
        except Exception as e:
            st.warning(f"Memory skipped: {e}")

        # Run Graph
        config = {"configurable": {"thread_id": st.session_state.thread_id}}
        inputs = {"messages": [HumanMessage(content=st.session_state.topic)], "research_data": []}
        
        # Stream events synchronously
        for event in agent_app.stream(inputs, config):
            
            if "Researcher" in event:
                data = event["Researcher"].get("research_data", [])
                st.session_state.research_data = data
                r_container.success(f"Found {len(data)} facts")
                with r_container.expander("Details"):
                    for d in data: st.write(d)
            
            if "Analyst" in event:
                # Handle varying output structures
                data = event["Analyst"].get("chart_data", [])
                st.session_state.chart_data = data
                a_container.success("Analysis Complete")
                
            if "Writer" in event:
                content = event["Writer"]["messages"][-1].content
                st.session_state.draft_content = content
                w_container.success("Draft Written")
        
        st.session_state.current_step = "reviewing"
        st.rerun()

    except Exception as e:
        st.error(f"CRASH REPORT: {e}")
        st.error("Check your terminal for detailed logs.")

# --- LOGIC: REVIEWING ---
if st.session_state.current_step == "reviewing":
    st.subheader("📝 Review Draft")
    
    tab1, tab2 = st.tabs(["Draft", "Data"])
    with tab1:
        st.components.v1.html(st.session_state.draft_content, height=600, scrolling=True)
    with tab2:
        st.write(st.session_state.research_data)

    feedback = st.text_input("Feedback (Optional):")
    
    if st.button("Submit Decision"):
        try:
            from agents import app as agent_app
            from langchain_core.messages import HumanMessage
            from memory_store import MemoryStore
            
            config = {"configurable": {"thread_id": st.session_state.thread_id}}
            
            if feedback:
                with st.spinner("Revising..."):
                    agent_app.update_state(config, {"messages": [HumanMessage(content=feedback)]})
                    for event in agent_app.stream(None, config): pass
                    
                    state = agent_app.get_state(config)
                    st.session_state.draft_content = state.values['messages'][-1].content
                    st.success("Revised!")
                    time.sleep(1)
                    st.rerun()
            else:
                # Save and Finish
                mem = MemoryStore()
                mem.save_memory(st.session_state.topic, st.session_state.draft_content)
                st.session_state.current_step = "finished"
                st.rerun()
        except Exception as e:
            st.error(f"Error submitting: {e}")

# --- LOGIC: FINISHED ---
if st.session_state.current_step == "finished":
    st.success("✅ Process Complete!")
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button("Download HTML", st.session_state.draft_content, "news.html", "text/html")
    with col2:
        if st.button("Start Over"):
            st.session_state.current_step = "idle"
            st.rerun()
            
    st.components.v1.html(st.session_state.draft_content, height=800)