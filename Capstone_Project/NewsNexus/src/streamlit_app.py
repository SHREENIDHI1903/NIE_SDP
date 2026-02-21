import streamlit as st
import os
import time
from datetime import datetime

# --- Import our Backend Logic ---
# We assume these files exist from previous steps
from ingestion import ingest_documents
from tools import get_llm_with_tools, lookup_policy_docs, web_search_stub
from agents import app as agent_app  # Import the graph we built
from memory_store import MemoryStore
from langchain_core.messages import HumanMessage

# --- Page Config ---
st.set_page_config(page_title="NewsNexus AI", page_icon="📰", layout="wide")

# --- Custom CSS for "Good HTML" Preview ---
st.markdown("""
<style>
    .main-header {font-size: 2.5rem; color: #1E3A8A; font-weight: bold;}
    .sub-header {font-size: 1.5rem; color: #4B5563;}
    .agent-box {border: 1px solid #ddd; padding: 15px; border-radius: 10px; margin-bottom: 10px; background-color: #f9f9f9;}
    .success-box {background-color: #D1FAE5; padding: 15px; border-radius: 10px; border: 1px solid #10B981;}
</style>
""", unsafe_allow_html=True)

# --- Session State Management ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "research_data" not in st.session_state:
    st.session_state.research_data = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = f"session_{int(time.time())}"
if "current_step" not in st.session_state:
    st.session_state.current_step = "idle" # idle, researching, reviewing, finished
if "draft_content" not in st.session_state:
    st.session_state.draft_content = ""

# --- Sidebar: Data Management ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2593/2593240.png", width=80)
    st.title("NewsNexus Control")
    st.divider()
    
    st.subheader("📂 Knowledge Base")
    uploaded_file = st.file_uploader("Upload Industry Report (PDF)", type="pdf")
    
    if uploaded_file:
        # Save file locally
        save_path = os.path.join("data/raw_pdfs", uploaded_file.name)
        os.makedirs("data/raw_pdfs", exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success(f"Saved: {uploaded_file.name}")
        
        if st.button("🧠 Process & Embed PDF"):
            with st.spinner("Chunking and Embedding... (This runs ingestion.py)"):
                # Call the ingestion function directly
                # Ensure ingestion.py is refactored to be callable or import logic here
                try:
                    ingest_documents() 
                    st.success("Vector Database Updated!")
                except Exception as e:
                    st.error(f"Error: {e}")

    st.divider()
    st.info("System Status: Ready\nModel: Llama 3.2 (Local)")

# --- Main Interface ---

st.markdown('<div class="main-header">📰 NewsNexus: Corporate Intelligence Agent</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Autonomous Multi-Agent System with Human-in-the-Loop</div>', unsafe_allow_html=True)
st.divider()

# Input Area
topic = st.text_input("Enter Research Topic:", placeholder="e.g., 'Impact of Generative AI on Banking sector 2024'")

if st.button("🚀 Start Agents") and topic:
    st.session_state.current_step = "researching"
    st.session_state.messages = [HumanMessage(content=topic)]
    st.session_state.research_data = []
    
    # Initialize Memory Store
    mem_store = MemoryStore()
    past_memory = mem_store.check_memory(topic)
    
    if "WARNING" in past_memory:
        st.warning(past_memory)
    else:
        st.success("No duplicates found in memory. Proceeding.")

# --- Visualization Logic ---

if st.session_state.current_step == "researching":
    
    # Create containers for real-time updates
    col1, col2, col3 = st.columns(3)
    with col1:
        research_status = st.status("🕵️ Researcher Agent", expanded=True)
    with col2:
        analyst_status = st.status("🧠 Analyst Agent", state="running", expanded=False)
    with col3:
        writer_status = st.status("✍️ Writer Agent", state="running", expanded=False)

    # Run the Graph Stream
    config = {"configurable": {"thread_id": st.session_state.thread_id}}
    inputs = {"messages": st.session_state.messages, "research_data": []}
    
    # We execute the graph step-by-step
    try:
        # Stream events from the graph
        print(f"\n[Streamlit] Starting graph for topic: '{topic}'")
        for event in agent_app.stream(inputs, config):
            print(f"[Streamlit] Event received: {list(event.keys())}")
            
            # --- Visualize Researcher ---
            if "Researcher" in event:
                research_output = event["Researcher"]
                findings = research_output.get("research_data", [])
                st.session_state.research_data = findings # Save for display
                
                research_status.write(f"Found {len(findings)} data points.")
                for item in findings:
                    with research_status.expander("View Finding"):
                        st.code(item)
                research_status.update(label="Researcher: Complete", state="complete", expanded=False)
                analyst_status.update(expanded=True) # Open next box

            # --- Visualize Analyst ---
            if "Analyst" in event:
                analyst_output = event["Analyst"]
                insight = analyst_output["messages"][-1].content
                analyst_status.write("Trends Identified:")
                analyst_status.info(insight[:200] + "...")
                analyst_status.update(label="Analyst: Complete", state="complete", expanded=False)
                writer_status.update(expanded=True)

            # --- Visualize Writer ---
            if "Writer" in event:
                writer_output = event["Writer"]
                draft = writer_output["messages"][-1].content
                st.session_state.draft_content = draft
                writer_status.write("Draft Generated.")
                writer_status.update(label="Writer: Complete", state="complete")
        
        # Move to Review Stage
        st.session_state.current_step = "reviewing"
        st.rerun()

    except Exception as e:
        print(f"[Streamlit] Error during graph execution: {str(e)}")
        st.error(f"Execution Error: {e}")
        import traceback
        st.code(traceback.format_exc())


# --- Review Stage (Human-in-the-Loop) ---
if st.session_state.current_step == "reviewing":
    st.subheader("📝 Draft Review")
    
    # Display HTML Preview
    with st.expander("View Rendered HTML", expanded=True):
        st.components.v1.html(st.session_state.draft_content, height=600, scrolling=True)
    
    col_a, col_b = st.columns([3, 1])
    
    with col_a:
        feedback = st.text_input("Feedback (Leave empty to approve):", placeholder="e.g., 'Make the tone more formal'")
    
    with col_b:
        st.write("") # Spacer
        st.write("") 
        if st.button("Submit Decision"):
            config = {"configurable": {"thread_id": st.session_state.thread_id}}
            
            if feedback:
                # REVISION LOOP
                st.info("Sending feedback to Writer...")
                agent_app.update_state(config, {"messages": [HumanMessage(content=feedback)]})
                
                # Resume Graph for Revision
                # Note: We need to handle the stream again similar to above, 
                # but for simplicity, we just run it and rerun the page
                for event in agent_app.stream(None, config):
                    pass # Let logic handle it
                
                # Fetch new state
                state = agent_app.get_state(config)
                st.session_state.draft_content = state.values['messages'][-1].content
                st.success("Draft Revised!")
                time.sleep(1)
                st.rerun()
                
            else:
                # APPROVAL
                st.session_state.current_step = "finished"
                
                # Save to Memory
                mem_store = MemoryStore()
                # Use the original topic if available, else generic
                topic_key = st.session_state.messages[0].content 
                mem_store.save_memory(topic_key, st.session_state.draft_content)
                
                st.rerun()

# --- Final Stage ---
if st.session_state.current_step == "finished":
    st.balloons()
    st.markdown('<div class="success-box">✅ Newsletter Approved & Archived!</div>', unsafe_allow_html=True)
    
    # Save to File
    filename = f"newsletter_{int(time.time())}.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(st.session_state.draft_content)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Download Button
        st.download_button(
            label="Download HTML File",
            data=st.session_state.draft_content,
            file_name=filename,
            mime="text/html"
        )
    
    with col2:
        # Link to open (User needs to open manually due to browser security, or we serve it)
        st.info(f"File saved locally as: {filename}")
        
    st.markdown("### Final Output Preview")
    st.components.v1.html(st.session_state.draft_content, height=800, scrolling=True)
    
    if st.button("Start New Research"):
        st.session_state.current_step = "idle"
        st.rerun()