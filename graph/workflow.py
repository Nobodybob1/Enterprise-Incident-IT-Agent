"""Build and compile the LangGraph workflow"""

from langgraph.graph import StateGraph, START, END
from graph.state import IncidentState
from graph.nodes import triage_node, diagnose_node, retrieve_node, propose_node

builder = StateGraph(IncidentState)

builder.add_node("triage", triage_node)
builder.add_node("diagnose", diagnose_node)
builder.add_node("retrieve", retrieve_node)
builder.add_node("propose", propose_node)

builder.add_edge(START, "triage")
builder.add_edge("triage", "diagnose")
builder.add_edge("diagnose", "retrieve")
builder.add_edge("retrieve", "propose")
builder.add_edge("propose", END)

workflow = builder.compile()

if __name__ == "__main__":
    result = workflow.invoke({"user_message": "the nginx server's disk is completely full, no space left on device"})
    print("\n=== Final Proposal ===")
    print(result["proposal"])