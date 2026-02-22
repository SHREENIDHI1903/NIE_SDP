# 🛠️ NewsNexus: Technical Walkthrough (Line-by-Line)

This document provides a deep dive into the NewsNexus codebase. Each script is explained block-by-block to help you understand the "why" behind the code.

---

## 1. `src/ingestion.py`
**Purpose**: Handles the "First Mile" of RAG—turning raw PDFs into searchable vectors.

*   **Lines 1-4**: Imports necessary for PDF loading (`PyPDFDirectoryLoader`), chunking (`RecursiveCharacterTextSplitter`), and Vector Storage (`Chroma`).
*   **Lines 11-15**: Loads all PDFs from the `data/raw_pdfs` folder. `loader.load()` returns a list of LangChain Document objects (one per page).
*   **Lines 19-25**: **Chunking Strategy**. Splits the long PDF text into 500-character chunks with a 50-character overlap. This ensures that a sentence split between two chunks isn't "lost."
*   **Lines 29-30**: **Stability Migration**. Initializes `OllamaEmbeddings(model="nomic-embed-text")`. This model has 768 dimensions and runs on the Ollama server to avoid local Torch crashes.
*   **Lines 34-45**: **Batching Logic**. Instead of sending 2000 chunks at once, we process them in groups of 100. This prevents the Ollama server from timing out and provides the user with real-time feedback (`Processing batch X of Y`).

---

## 2. `src/retrieval.py`
**Purpose**: The "Search Engine" of the Knowledge Base.

*   **Line 13**: Initializes the 768-dim Ollama embedding model (must match `ingestion.py`).
*   **Lines 17-21**: Connects to the existing Chroma database at `DB_PATH`.
*   **Line 27**: `similarity_search_with_score`. This is the core RAG step. It converts the user's question into a vector and finds the "closest" matches in the database.
*   **Lines 29-32**: Returning the top `k` most similar snippets for the LLM to read.

---

## 3. `src/tools.py`
**Purpose**: Defines the "Hands" of the Agent (Web, RSS, and RAG).

*   **`lookup_policy_docs` (Lines 8-27)**: A wrapper around `retrieval.py`. It adds "Deep-Links" (`file:///...`) to the research results so you can click the source PDF directly in the chat.
*   **`web_search_stub` (Lines 31-64)**: 
    *   **Logic**: Uses the `DDGS` library.
    *   **Resilience**: Tries a standard text search first. If that yields nothing, it automatically tries a **News search** (better for current events like "AI Summits").
*   **`rss_feed_search` (Lines 66-93)**: Scans a list of specialized industry RSS feeds (TechCrunch, OpenAI, etc.). It uses broad keyword matching to find recent technical insights.

---

## 4. `src/agents.py`
**Purpose**: Defines the "Brains" and the Workflow (LangGraph).

*   **`AgentState` (Lines 12-17)**: The "Memory" of the graph. It tracks the message history, the raw research findings, and numeric chart data as they pass from one agent to another.
*   **`researcher_node` (Lines 23-81)**:
    *   Decides which tool to call based on the user's request.
    *   **Parsing Logic**: Contains a custom "cleaner" (Lines 50-64) that handles complex schemas from Llama 3.2, ensuring tool arguments are simple strings.
*   **`analyst_node` (Lines 83-121)**:
    *   Reads the raw research data.
    *   **Data Viz Extraction**: Uses a regex to find structured JSON blocks (` ```json ... ``` `). If found, it saves this to the `chart_data` state for Plotly to render.
*   **`writer_node` (Lines 123-144)**: Formats the analysis into a professional HTML newsletter. It is given a strict instruction to **preserve all source links**.

---

## 5. `src/memory_store.py`
**Purpose**: Manages long-term archive to prevent duplicate research.

*   **`MemoryStore.__init__`**: Connects to a *separate* Chroma database (`archive_memory`).
*   **`save_memory`**: Triggered only after a human approves a newsletter. It archives the final HTML.
*   **`check_memory`**: Runs *before* research starts. It checks if we've written about this topic recently. If the similarity score is < 0.4, it issues a **Duplicate Warning**.

---

## 6. `src/phase5_final.py`
**Purpose**: The CLI Orchestrator (Complete Application).

*   **`researcher_with_memory_node`**: A specialized version of the researcher that reads from `MemoryStore` BEFORE deciding to search.
*   **`human_approval_node`**: Creates a "Gate." The graph stops here and waits for your input in the terminal.
*   **Main Loop (Lines 118-154)**:
    1.  Asks for a topic.
    2.  Runs the Agents up to the Approval Gate.
    3.  Displays the draft.
    4.  If approved, triggers `memory_store.save_memory()`.

---

## 7. `src/streamlit_app.py`
**Purpose**: The "Front Door" (Web UI).

*   **`st.sidebar`**: Displays the Knowledge Base status and all PDFs found in your data folder.
*   **`ingest_documents` trigger**: Detects if the database is missing and automatically runs the ingestion logic with a loading bar.
*   **The Orchestration Loop**: Manages the multi-step state machine (Researching -> Analyzing -> Review).
*   **Visualization**: Uses `st.plotly_chart` to render any data extracted by the Analyst node.
*   **PDF Export**: Uses `xhtml2pdf` to convert the final HTML newsletter into a downloadable PDF document.

---

**🎓 Note**: This modular architecture (Tools -> Nodes -> Graph -> UI) is the industrial standard for building stable, scalable AI Agent systems.
