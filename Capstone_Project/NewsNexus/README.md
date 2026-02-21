
# 📰 NewsNexus: Autonomous Corporate Intelligence Agent
### Capstone Project | Student Development Program (SDP)

**NewsNexus** is a local, privacy-first **Agentic AI System** designed to act as an automated corporate analyst. It autonomously researches topics using internal documents (PDFs) and a simulated web search, analyzes trends, and drafts professional HTML newsletters—all while keeping a human in the loop for final approval.



## 🏗️ Architecture Overview

This project was built in **5 Phases**, moving from basic RAG to advanced Multi-Agent Orchestration.

**The "CPU-Friendly" Tech Stack:**
* **LLM Engine:** [Ollama](https://ollama.com/) (running Llama 3.2 or Qwen 2.5)
* **Orchestration:** [LangGraph](https://langchain-ai.github.io/langgraph/) (Stateful Multi-Agent Workflows)
* **Vector Database:** [ChromaDB](https://www.trychroma.com/) (Local persistent storage)
* **Embeddings:** [HuggingFace](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) (Sentence Transformers)
* **Language:** Python 3.10+

---

## 🚀 Setup & Installation

### 1. Prerequisites
* Python installed.
* [Ollama](https://ollama.com/) installed and running.

### 2. Environment Setup
```bash
# Clone the repository (or create folder)
mkdir NewsNexus
cd NewsNexus

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

```

### 3. Model Pull

We need a model capable of **Function Calling**.

```bash
ollama pull llama3.2

```

---

## 📚 Phase-by-Phase Implementation Guide

### 🔹 Phase 1: The Knowledge Base (RAG)

**Goal:** Give the AI "Long-term Knowledge" by ingesting PDF reports.

* **Concept:** We use **Recursive Character Chunking** to split PDFs into manageable pieces and **Sentence Transformers** to convert them into vectors.
* **Key Files:**
* `src/ingestion.py`: Reads PDFs from `data/raw_pdfs/` and saves vectors to `data/chroma_db/`.
* `src/retrieval.py`: Performs Semantic Search + Keyword Boosting (Hybrid Search).


* **Run it:**
```bash
# Put a PDF in data/raw_pdfs first!
python src/ingestion.py

```



### 🔹 Phase 2: Tool Definition (Function Calling)

**Goal:** Give the LLM "Hands" to interact with the world.

* **Concept:** We define Python functions that the LLM can "decide" to call.
* **The Tools:**
1. `lookup_policy_docs`: Queries the Chroma vector DB.
2. `web_search_stub`: A simulated internet search (returns deterministic JSON for workshop stability).


* **Key File:** `src/tools.py`
* **Run it:**
```bash
python src/tools.py
# Output: You should see the Agent choosing different tools based on your query.

```



### 🔹 Phase 3: Multi-Agent Orchestration

**Goal:** Create a team of specialized agents working in a pipeline.

* **Concept:** Using **LangGraph** to build a State Machine (DAG).
* **The Team:**
* 🕵️ **Researcher:** Uses tools to find raw data.
* 🧠 **Analyst:** Reads raw data and identifies 3 key trends.
* ✍️ **Writer:** Formats trends into an HTML newsletter.


* **Flow:** `Researcher -> Analyst -> Writer -> END`
* **Key File:** `src/agents.py`
* **Run it:**
```bash
python src/agents.py

```



### 🔹 Phase 4: Human-in-the-Loop (HITL)

**Goal:** Add a safety check before publishing.

* **Concept:** Using **Interrupts** and **MemorySaver**. The graph pauses execution to wait for user input.
* **The Workflow:**
1. Agents generate a draft.
2. System PAUSES at the "Approval Gate".
3. Human provides feedback (e.g., "Too long, rewrite it").
4. System routes back to the **Writer** to fix it.


* **Key File:** `src/phase4_human_loop.py`
* **Run it:**
```bash
python src/phase4_human_loop.py

```



### 🔹 Phase 5: Memory & Persistence (Final)

**Goal:** Prevent the AI from repeating itself.

* **Concept:** We add a second Vector Store (`archive_memory`) to store *generated* newsletters. The Researcher checks this before starting work.
* **Mechanism:**
* *Before Researching:* "Have I written about this topic in the last 7 days?"
* *After Approval:* Save the final HTML to the archive.


* **Key Files:**
* `src/memory_store.py`: Manages the archive database.
* `src/phase5_final.py`: The complete application.


* **Run it:**
```bash
python src/phase5_final.py

```



---

## 📂 Project Structure

```text
NewsNexus/
├── data/
│   ├── raw_pdfs/            # Drop your PDFs here
│   ├── chroma_db/           # Created by ingestion.py (Knowledge Base)
│   └── archive_memory/      # Created by phase5_final.py (Long-term Memory)
├── src/
│   ├── agents.py            # The Agent Graph Definitions
│   ├── ingestion.py         # PDF -> Vector Logic
│   ├── retrieval.py         # Search Logic
│   ├── tools.py             # Tool Definitions (Search Stub, etc.)
│   ├── memory_store.py      # Archive Logic
│   ├── phase4_human_loop.py # HITL Script
│   └── phase5_final.py      # FINAL CAPSTONE APPLICATION
├── requirements.txt         # Dependencies
└── README.md                # This file

```

---

## ⚠️ Troubleshooting

**1. "Registry... does not support tools"**

* *Cause:* You are using a model like `gemma:2b` or `llama2`.
* *Fix:* Run `ollama pull llama3.2` and update your code to use `model="llama3.2"`.

**2. "No specific data found"**

* *Cause:* The `web_search_stub` in `tools.py` has a limited mock database.
* *Fix:* Open `src/tools.py` and add your topic to the `mock_database` dictionary, or rely on the fallback message.

**3. "ChromaDB errors"**

* *Cause:* Version mismatch or file lock.
* *Fix:* Delete the `data/chroma_db` folder and re-run `python src/ingestion.py`.

---

**🎓 Education Note:** This project demonstrates the transition from *Prompt Engineering* (Day 1) to *Agentic Systems* (Day 6), providing a complete blueprint for modern AI development.
