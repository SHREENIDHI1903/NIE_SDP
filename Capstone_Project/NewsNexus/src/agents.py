import operator
from typing import Annotated, List, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END

# Import our tools and LLM setup from Phase 2
from tools import get_llm_with_tools, lookup_policy_docs, web_search_stub, rss_feed_search

# --- 1. Define the State (Enhanced for Visualization) ---
# AgentState is a custom TypedDict that defines the structure of data flowing between nodes.
class AgentState(TypedDict):
    # operator.add ensures we append new messages instead of overwriting existing ones.
    messages: Annotated[List[BaseMessage], operator.add]
    research_data: List[str]
    chart_data: List[dict] # New: Stores structured data for Plotly

# Initialize Resources
llm, llm_with_tools, tools = get_llm_with_tools()

# --- 2. Define the Nodes / Agent Personas ---

def researcher_node(state: AgentState):
    """
    Agent 1: Researcher (Enhanced with Dynamic Orchestration)
    Responsibility: Create an elaborate research plan and execute detailed sub-queries.
    """
    print("\n--- [Agent: Researcher] is gathering comprehensive data ---")
    last_message = state["messages"][-1]
    topic = last_message.content

    print(f"   > Topic: {topic}")
    
    # 1. Ask the LLM to break down the topic into an advanced research plan
    plan_prompt = f"""You are an elite Research Director. 
The user wants an elaborate and advanced level report on: '{topic}'.
Break this topic down into exactly 3 specific, diverse search queries that cover different angles (e.g., technical, market, news).
Just output the 3 queries separated by a pipe character (|). Do not include any other text or explanation."""
    
    try:
        plan_response = llm.invoke(plan_prompt)
        content = plan_response.content.replace('\n', '')
        queries = [q.strip() for q in content.split('|') if q.strip()]
        if len(queries) < 1: 
            queries = [topic, f"{topic} latest news", f"{topic} technical analysis"]
    except Exception as e:
        print(f"   > Plan generation failed: {e}. Using fallbacks.")
        queries = [topic, f"{topic} latest news", f"{topic} technical analysis"]

    # Ensure we max out at 3 to save time but remain elaborate
    queries = queries[:3]
    print(f"   > Research Plan Queries: {queries}")

    research_findings = []
    
    # 2. Iterate through queries and force comprehensive data gathering using our tools directly
    for i, q in enumerate(queries, 1):
        print(f"   > [Executing Phase {i}/3] Searching for angle: {q}")
        
        # Web Search
        try:
            web_res = web_search_stub.invoke(q)
            if "0 results" not in web_res and "Error" not in web_res:
                research_findings.append(f"Source: Web Search (Query: {q})\nData: {web_res}")
        except Exception as e:
            print(f"     > Web Search error: {e}")
            
        # RSS Search
        try:
            rss_res = rss_feed_search.invoke(q)
            if "No matching" not in rss_res:
                research_findings.append(f"Source: RSS Feeds (Query: {q})\nData: {rss_res}")
        except Exception as e:
            print(f"     > RSS error: {e}")
            
    # 3. Always check internal docs for the MAIN topic (RAG)
    try:
        doc_res = lookup_policy_docs.invoke(topic)
        if "No relevant" not in doc_res:
             research_findings.append(f"Source: Internal Database (Topic: {topic})\nData: {doc_res}")
    except Exception:
        pass

    if not research_findings:
        research_findings.append("AGENT: Could not find significant new data. Returning base knowledge.")

    print(f"   > Researcher found {len(research_findings)} comprehensive items.")
    
    from langchain_core.messages import AIMessage
    msg = AIMessage(content=f"I have completed a comprehensive research plan using {len(queries)} diverse queries: {', '.join(queries)}. I found {len(research_findings)} distinct data sources.")

    return {
        "messages": [msg], 
        "research_data": research_findings
    }

def analyst_node(state: AgentState):
    """
    Agent 2: Analyst (Enhanced with Data Extraction)
    Responsibility: Identify key trends AND extract numeric data for plotting.
    """
    print("\n--- [Agent: Analyst] is identifying trends ---")
    raw_data = "\n\n".join(state["research_data"])
    
    # Note: We use a standard LLM invocation here (no tools bound)
    # because the Analyst only needs to think, not act.
    prompt = f"""You are a senior expert analyst. 
    1. Provide an elaborative, advanced synthesis of the raw data. Identify 4-5 key trends and explain their deep implications.
    2. DATA VIZ EXTRACTION: Look for REAL numeric trends (percentages, market sizes, years).
       If you find numeric data, extract it into a JSON block like this:
       ```json
       [{{ "label": "2024", "value": 50 }}, {{ "label": "2025", "value": 75 }}]
       ```
    
    CRITICAL: If the raw data is empty or insufficient, DO NOT make up hypothetical numbers. Only extract data that is EXPLICITLY present.
    
    Here is the comprehensive research data gathered across multiple sub-queries and platforms:
    {raw_data}
    """
    
    print(f"   > Analyst node invoking base LLM with {len(raw_data)} chars of raw data...")
    response = llm.invoke(prompt)
    print(f"   > Analyst response received.")
    content = response.content
    
    # Extract JSON if present for Plotly
    chart_data = []
    import json
    import re
    json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
    if json_match:
        try:
            chart_data = json.loads(json_match.group(1))
        except:
            pass
            
    return {"messages": [response], "chart_data": chart_data}

def writer_node(state: AgentState):
    """
    Agent 3: Writer (Enhanced for Citations)
    Responsibility: Format analysis into HTML while preserving deep links.
    """
    print("\n--- [Agent: Writer] is formatting the newsletter ---")
    analyst_insight = state["messages"][-1].content
    
    prompt = f"""You are an elite technology newsletter editor. 
    Compile the advanced analysis into an elaborate, professional HTML format.
    Make it look like a premium Substack or TechCrunch deep-dive. Use semantic HTML, clean structured headings, bullet points, and sophisticated language.
    
    CRITICAL: Preserve all links provided in the analysis (e.g., [Title](URL)).
    Format them as clickable <a> tags in the HTML. DO NOT wrap the output in markdown code blocks (e.g. ```html), ONLY return raw HTML.
    
    TRENDS & ANALYSIS:
    {analyst_insight}
    """
    
    print(f"   > Writer node invoking base LLM with {len(analyst_insight)} chars of insight...")
    response = llm.invoke(prompt)
    print(f"   > Writer response received.")
    return {"messages": [response]}

# --- 3. Build the Graph ---
# Use StateGraph to define the nodes and how they connect.
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("Researcher", researcher_node)
workflow.add_node("Analyst", analyst_node)
workflow.add_node("Writer", writer_node)

# Add Edges (Define the linear flow)
# Start -> Researcher -> Analyst -> Writer -> End.
workflow.set_entry_point("Researcher")
workflow.add_edge("Researcher", "Analyst")
workflow.add_edge("Analyst", "Writer")
workflow.add_edge("Writer", END)

# Compile the graph
app = workflow.compile()

# --- 4. Runnable Test Block ---
if __name__ == "__main__":
    user_topic = "latest AI trends and internal productivity reports"
    print(f"Starting NewsNexus Agent Team on topic: '{user_topic}'...")
    
    inputs = {"messages": [HumanMessage(content=user_topic)], "research_data": []}
    
    # Run the graph and stream the output
    for output in app.stream(inputs):
        pass # The nodes will print their own status
    
    print("\n\n=== FINAL NEWSLETTER (HTML) ===")
    print(output['Writer']['messages'][-1].content)