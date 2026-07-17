"""
Full workflow with a real human-approval gate.
"""

import uuid
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from graph.state import IncidentState
from graph.nodes import (
    triage_node,
    diagnose_node,
    retrieve_node,
    propose_node,
    await_approval_node,
    execute_action_node
)

builder = StateGraph(IncidentState)
builder.add_node("triage", triage_node)
builder.add_node("diagnose", diagnose_node)
builder.add_node("retrieve", retrieve_node)
builder.add_node("propose", propose_node)
builder.add_node("await_approval", await_approval_node)
builder.add_node("execute_action", execute_action_node)

builder.add_edge(START, "triage")
builder.add_edge("triage", "diagnose")
builder.add_edge("diagnose", "retrieve")
builder.add_edge("retrieve", "propose")
builder.add_edge("propose", "await_approval")
builder.add_edge("await_approval", "execute_action")
builder.add_edge("execute_action", END)

# A checkpointer is required for interrupt() to work at all.
# InMemorySaver is fine for local learning. A real deployment would use
# a database-backed checkpointer instead, so pauses survive a restart.
checkpointer = InMemorySaver()
workflow = builder.compile(checkpointer=checkpointer)

if __name__ == "__main__":
    # thread_id identifies THIS specific incident run, so we can come back
    # to the exact same paused execution later.
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    result = workflow.invoke(
        {"user_message": "auth-service seems really slow and unresponsive"},
        config=config
    )

    # If the graph paused, it'll show up under "__interrupt__"
    if "__interrupt__" in result:
        interrupt_info = result["__interrupt__"][0].value
        print("\n=== PAUSED FOR HUMAN APPROVAL ===")
        print(interrupt_info["proposal"])
        print(f"\n{interrupt_info['question']}")

        answer = input("Your answer (yes/no): ").strip()

        # Resume the SAME thread with the human's answer
        final_result = workflow.invoke(Command(resume=answer), config=config)

        print("\n=== Final Outcome ===")
        print(final_result["action_result"])
    else:
        print("\n=== Final Proposal (no approval needed?) ===")
        print(result["proposal"])