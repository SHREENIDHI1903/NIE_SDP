import json
from langchain.tools import tool
from langchain_ollama import ChatOllama
from retrieval import retrieve_documents

# --- Tool 1: The RAG Tool ---
@tool
def lookup_policy_docs(query: str) -> str:
    """
    Useful for finding specific details, statistics, or sections from the uploaded 
    industry reports (PDFs). Use this when you need factual grounding.
    """
    # Clean the query if it comes in as a dictionary string
    if isinstance(query, str) and "{" in query:
        # Simple cleanup to remove JSON-like artifacts if the LLM gets confused
        query = query.replace("{", "").replace("}", "").replace("value:", "")
        
    docs = retrieve_documents(query, k=3)
    results = []
    for doc, score in docs:
        results.append(f"Content: {doc.page_content}\nSource: {doc.metadata.get('source')}")
    return "\n\n".join(results) if results else "No relevant documents found."

# --- Tool 2: The Web Search Stub (Robust Version) ---
@tool
def web_search_stub(query: str) -> str:
    """
    Useful for finding 'latest' or 'current' news that might not be in the PDFs.
    Use this for recent trends or real-time events.
    """
    # 1. Clean up the input (Llama 3.2 sometimes passes JSON strings)
    clean_query = str(query).lower()
    print(f"\n[Tool Called] Web Search Stub for: '{clean_query}'")
    
    # 2. Expanded Mock Database
    mock_database = {
        "trends": {
            "title": "Top AI Trends of 2024",
            "snippet": "1. Multimodal AI is rising. 2. Small Language Models (SLMs) are gaining popularity. 3. AI Regulation is tightening in EU."
        },
        "productivity": {
            "title": "AI Impact on Productivity",
            "snippet": "New studies show AI coding assistants increase developer velocity by 55%. Administrative tasks are reduced by 40%."
        },
        "competitors": {
            "title": "Market Competitors",
            "snippet": "Major players include OpenAI, Google DeepMind, Anthropic, and open-source leaders like Meta (Llama) and Mistral."
        },
        "nvidia": {
            "title": "NVIDIA Corp Market Data",
            "snippet": "NVIDIA stock remains volatile but high due to GPU demand for data centers."
        }
    }
    
    # 3. Fuzzy Matching
    results = []
    for key, data in mock_database.items():
        if key in clean_query:
            results.append(data)
            
    # 4. Fallback (CRITICAL FIX: Always return something!)
    if not results:
        return json.dumps({
            "title": "General AI News",
            "snippet": "AI adoption is accelerating across all sectors. Companies are focusing on RAG and Agentic workflows."
        })
            
    return json.dumps(results)

def get_llm_with_tools():
    # Use llama3.2 which supports tool binding
    llm = ChatOllama(model="llama3.2", temperature=0) 
    tools = [lookup_policy_docs, web_search_stub]
    llm_with_tools = llm.bind_tools(tools)
    return llm, llm_with_tools, tools

# --- Test Block ---
if __name__ == "__main__":
    print("Initializing Agent with Tools...")
    base_llm, agent, tools_list = get_llm_with_tools()
    
    # Test Query 1: Should trigger RAG Tool
    query1 = "What do the internal reports say about Generative AI productivity?"
    print(f"\nUser: {query1}")
    response1 = agent.invoke(query1)
    print(f"Agent Decision: {response1.tool_calls}") 
    # Expected: [{'name': 'lookup_policy_docs', 'args': {'query': '...'}}]

    # Test Query 2: Should trigger Web Search Tool
    query2 = "What are the latest AI trends in 2024?"
    print(f"\nUser: {query2}")
    response2 = agent.invoke(query2)
    print(f"Agent Decision: {response2.tool_calls}")
    # Expected: [{'name': 'web_search_stub', 'args': {'query': '...'}}]