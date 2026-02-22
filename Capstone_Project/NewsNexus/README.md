# 📰 NewsNexus: Autonomous Corporate Intelligence Agent
### Capstone Project | Professional Intelligence Edition

**NewsNexus** is a local, privacy-first **Agentic AI System** designed to act as an automated corporate analyst. It autonomously researches topics using internal documents (PDFs), live web search, and targeted industry RSS feeds. It analyzes trends, generates interactive visualizations, and drafts professional reports available for HTML and PDF export.

---

## 🏗️ Architecture Overview

The system uses a **Multi-Agent Orchestration** flow powered by **LangGraph**, enabling complex reasoning and human-in-the-loop validation.

**The "Stability-First" Tech Stack:**
* **LLM Engine:** [Ollama](https://ollama.com/) (Llama 3.2 3B)
* **Embeddings Engine:** [Ollama](https://ollama.com/) (**nomic-embed-text**) - *Migrated from local Torch for Windows stability.*
* **Orchestration:** [LangGraph](https://langchain-ai.github.io/langgraph/)
* **Vector Database:** [ChromaDB](https://www.trychroma.com/)
* **UI Interface:** [Streamlit](https://streamlit.io/)
* **Search Tools:** DuckDuckGo (Live Search), Feedparser (RSS), RAG (PDFs)

---

## 🚀 Setup & Installation

### 1. Prerequisites
* Python 3.10+
* [Ollama](https://ollama.com/) installed and running.

### 2. Environment Setup
```bash
# Clone the repository (or create folder)
git clone https://github.com/SHREENIDHI1903/NIE_SDP.git
cd NIE_SDP/NewsNexus

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 3. Mandatory Model Pull
You must pull both the **LLM** and the **Embedding Model** to ensure stability:
```bash
ollama pull llama3.2
ollama pull nomic-embed-text
```

---

## 🌟 Pro Edition Features

*   **📊 Interactive Visualizations**: Automatic detection of numeric trends rendered as **Plotly Bar Charts**.
*   **📡 Multi-Source Research**: Combines PDFs with live DuckDuckGo results and targeted RSS feeds (MIT Tech Review, OpenAI).
*   **📄 Professional Export**: Download final reports as **PDF** or HTML files.
*   **🔗 Citation Deep-Links**: Clickable links for both web sources and local PDF files for full transparency.

---

## 📚 Phase-by-Phase Implementation Guide

### 🔹 Phase 1: The Knowledge Base (RAG)

**Goal:** Give the AI "Long-term Knowledge" by ingesting PDF reports.

* **Concept:** We use **Recursive Character Chunking** and **Ollama Embeddings** to turn PDFs into searchable vectors.
* **Key Files:**
* `src/ingestion.py`: Reads PDFs from `data/raw_pdfs/` and saves vectors to `data/chroma_db/`.
* `src/retrieval.py`: Performs Semantic Search + Keyword Boosting.

* **Run it:**
```bash
# Put a PDF in data/raw_pdfs first!
python src/ingestion.py
```

### 🔹 Phase 2: Tool Definition (Function Calling)

**Goal:** Give the LLM "Hands" to interact with the world.

* **Concept:** We define Python functions that the LLM can "decide" to call.
* **The Tools:**
1. `lookup_policy_docs`: Queries the Chroma vector DB with deep-link support.
2. `web_search_stub`: Performs a **Live DuckDuckGo Search** for real-time news.
3. `rss_feed_search`: Scans industry feeds for specialized technical insights.

* **Key File:** `src/tools.py`

### 🔹 Phase 3: Multi-Agent Orchestration

**Goal:** Create a team of specialized agents working in a pipeline.

* **Concept:** Using **LangGraph** to build a State Machine.
* **The Team:**
* 🕵️ **Researcher:** Gathers data from PDF, Web, and RSS.
* 🧠 **Analyst:** Identifies trends and extracts numeric data for charts.
* ✍️ **Writer:** Formats trends into professional HTML while preserving citations.

* **Flow:** `Researcher -> Analyst -> Writer -> END`
* **Key File:** `src/agents.py`

### 🔹 Phase 4: Human-in-the-Loop (HITL)

**Goal:** Add a safety check before publishing.

* **Concept:** The graph pauses at an "Approval Gate," allowing humans to provide feedback for revisions.
* **Key File:** `src/phase4_human_loop.py`

### 🔹 Phase 5: Memory & Persistence

**Goal:** Prevent the AI from repeating itself.

* **Concept:** Uses an `archive_memory` store to check if a research topic has been covered recently.
* **Key Files:** `src/memory_store.py` and `src/phase5_final.py`.

---

## 📂 Project Structure

```text
NewsNexus/
├── .streamlit/              # Launch Stability Config
├── data/
│   ├── raw_pdfs/            # Drop your PDFs here
│   ├── chroma_db/           # Knowledge Base (Vector DB)
│   └── archive_memory/      # Long-term Memory
├── src/
│   ├── streamlit_app.py     # MAIN APP ENTRY POINT
│   ├── agents.py            # Agent Graph Definitions
│   ├── ingestion.py         # PDF Ingestion Logic
│   ├── retrieval.py         # Search & Retrieval Logic
│   ├── tools.py             # Tools (Web, RSS, RAG)
│   └── memory_store.py      # Archive/Memory Management
└── requirements.txt         # Dependencies
```

---

## 🎮 How to Run

1. **Start the UI:**
   ```bash
   cd src
   streamlit run streamlit_app.py
   ```
2. **Setup Library**: Drop PDFs into the sidebar to build your knowledge base.
3. **Research**: Enter a topic like "AI Trends in 2026" and watch the agents collaborate!

---

## ⚠️ Troubleshooting

**1. "Disconnect" Errors on Windows**
* *Fix:* Ensure you are running the app from the `src/` folder. I have added a configuration in `src/.streamlit/config.toml` that disables the file watcher to prevent disconnects during database updates.

**2. "Torch/DLL" Error**
* *Fix:* We have migrated the system to **Ollama Embeddings**. Ensure you have run `ollama pull nomic-embed-text`.

---

**🎓 Education Note:** This project demonstrates a production-oriented transition from basic RAG to a tool-equipped **Agentic Workflow**, providing a blueprint for modern AI development.
