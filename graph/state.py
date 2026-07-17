"""
Shared state that flows though the LangGraph workflow.
Each node reads from this and returns updates to merge into it.
"""

from typing import TypedDict, Optional

class IncidentState(TypedDict):
    user_message: str
    service_name: Optional[str]
    runbook_context: Optional[str]
    tool_result: Optional[str]
    proposal: Optional[str]