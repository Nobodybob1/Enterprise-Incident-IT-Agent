"""
The four workflow nodes: triage, retrieve, diagnose, propose.
"""

import os
import json
from anthropic import Anthropic
from dotenv import load_dotenv

from rag.retrieve import retrieve
from tools.mock_tools import check_service_status, MOCK_SERVICES
from langgraph.types import interrupt

load_dotenv()
client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
MODEL = "claude-sonnet-5"

KNOWN_SERVICES = list(MOCK_SERVICES.keys())

def _extract_text(response):
    """Return the first text block's content, skipping thinking/tool blocks."""
    for block in response.content:
        if block.type == "text":
            return block.text
    raise ValueError(f"No text block in response content: {response.content}")

def triage_node(state):
    """Figure out which known service the user is asking about."""
    prompt = (
        f"Known services: {KNOWN_SERVICES}\n"
        f"User message: \"{state['user_message']}\"\n\n"
        "Which known service is the user asking about? "
        "Reply with ONLY the exact service name from the list, nothing else. "
        "If none match, reply with exactly: unknown"
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=20,
        messages=[{"role": "user", "content": prompt}],
    )
    service_name = _extract_text(response).strip().lower()
    print(f"[Triage] Detected service: {service_name}")
    return {"service_name": service_name}

def diagnose_node(state):
    """Check the live (mock) status of the identified service."""
    result = check_service_status(state["service_name"])
    print(f"[Diagnose] Tool result: {result}")
    return {"tool_result": result}

def retrieve_node(state):
    """Pull the most relevant runbook for this incident - using the live status to sharpen the search"""
    tool_result = state.get("tool_result") or {}
    status_summary = f"{tool_result.get('status', '')} CPU {tool_result.get('cpu_percent', '')}%"

    # Combine the user's original wording with concrete live data.
    # This lets retrieval match on facts (e.g. "degraded CPU 91%")
    # even if the user;s own phrasing was vague.
    search_query = f"{state['user_message']} {status_summary}"

    matches = retrieve(search_query, top_k=3, min_score=0.3)
    if matches:
        labeled_parts = []
        for m in matches:
            label = "RUNBOOK" if m["source"] == "runbook" else "PAST INCIDENT TICKET"
            labeled_parts.append(f"[{label}: {m['filename']}]\n{m['text']}")
        context = "\n\n---\n\n".join(labeled_parts)
    else:
        context = "No sufficiently relevant runbook or past ticket found."

    print(f"[Retrieve] Search query used: '{search_query}'")
    print(f"[Retrieve] Sources used: {[(m['source'], m['filename'], round(m['score'], 3)) for m in matches]}")
    return {"runbook_context": context}

def propose_node(state):
    """Ask Claude to propose a fix, grounded in the runbook + live status."""
    prompt = (
        f"User's incident report: \"{state['user_message']}\"\n\n"
        f"Relevant runbook(s) and/or past incident tickets:\n{state['runbook_context']}\n\n"
        f"Live service status: {json.dumps(state['tool_result'])}\n\n"
        "Based on the information above, propose a specific fix. Be concise. "
        "If a runbook is present, treat it as the official procedure and "
        "reference its steps where relevant. If a past incident ticket is "
        "also present, you may mention how a similar incident was resolved "
        "before, but the runbooks's steps take priority if the two suggest "
        "different actions."
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    proposal = _extract_text(response)
    return {"proposal": proposal}

def await_approval_node(state):
    """
    Pause here and wait for a human yes/no on the proposed action.
    """
    decision = interrupt({
        "question": f"Approve the proposed action for {state['service_name']}?",
        "proposal": state['proposal']
    })
    approved = str(decision).strip().lower() in ("yes", "y", "approve")
    return {"approved": approved}

def execute_action_node(state):
    """
    Mock 'execute' step. We never actually restart anything real -
    this just simulates what would happen, gated entirely by human approval.
    """
    if state.get("approved"):
        result = f"[MOCK ACTION] Restarting {state['service_name']}... done (simulated)."
    else:
        result = f"[CANCELLED] No action taken on {state['service_name']}. Flagged for further human review."
    print(f"[Execute] {result}")
    return {"action_result": result}