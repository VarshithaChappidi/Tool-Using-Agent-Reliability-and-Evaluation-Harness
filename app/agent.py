from __future__ import annotations
import time
from typing import TypedDict
from langgraph.graph import StateGraph, END
from app.schemas import AgentRequest, AgentOutcome
from app.tools import MockSupportAPI

MAX_RETRIES = 2

class State(TypedDict, total=False):
    request: dict
    attempts: int
    errors: list[str]
    ticket_status: str
    status: str
    summary: str
    proposed_action: str | None
    started: float

def build_graph(api: MockSupportAPI):
    def classify(state: State):
        msg = state["request"]["user_message"].lower()
        scenario = state["request"]["scenario"]
        if scenario == "prompt_injection" or any(x in msg for x in ["ignore all rules", "bypass approval", "reveal system prompt"]):
            return {"status": "blocked", "summary": "Untrusted instruction detected; workflow policy was not changed.", "proposed_action": None}
        if not state["request"]["ticket_id"] or any(x in msg for x in ["maybe", "not sure", "something"]):
            return {"status": "needs_clarification", "summary": "Please clarify the ticket and the exact support action requested.", "proposed_action": None}
        return {"status": "continue"}

    def retrieve(state: State):
        result = api.get_ticket(state["request"]["ticket_id"], state["request"]["scenario"])
        attempts = state.get("attempts", 0) + 1
        errors = list(state.get("errors", []))
        if not result.ok:
            errors.append(result.error or "unknown_tool_error")
            if result.retryable and attempts < MAX_RETRIES:
                return {"attempts": attempts, "errors": errors, "status": "retry"}
            return {"attempts": attempts, "errors": errors, "status": "tool_failed", "summary": f"Ticket lookup failed: {result.error}", "proposed_action": None}
        return {"attempts": attempts, "ticket_status": result.status, "status": "retrieved"}

    def draft(state: State):
        ticket_id = state["request"]["ticket_id"]
        status = state.get("ticket_status", "unknown")
        return {"status": "completed", "summary": f"Ticket {ticket_id} is currently {status}. A proposed follow-up has been drafted.", "proposed_action": f"Review ticket {ticket_id} and consider an update after human approval."}

    def route_classify(state: State):
        return "retrieve" if state.get("status") == "continue" else END

    def route_retrieve(state: State):
        if state.get("status") == "retry": return "retrieve"
        if state.get("status") == "retrieved": return "draft"
        return END

    graph = StateGraph(State)
    graph.add_node("classify", classify)
    graph.add_node("retrieve", retrieve)
    graph.add_node("draft", draft)
    graph.set_entry_point("classify")
    graph.add_conditional_edges("classify", route_classify, {"retrieve": "retrieve", END: END})
    graph.add_conditional_edges("retrieve", route_retrieve, {"retrieve": "retrieve", "draft": "draft", END: END})
    graph.add_edge("draft", END)
    return graph.compile()

def run_agent(request: AgentRequest, api: MockSupportAPI | None = None) -> tuple[AgentOutcome, float]:
    api = api or MockSupportAPI()
    graph = build_graph(api)
    started = time.perf_counter()
    state = graph.invoke({"request": request.model_dump(), "attempts": 0, "errors": []})
    elapsed = (time.perf_counter() - started) * 1000
    outcome = AgentOutcome(
        status=state.get("status", "tool_failed"),
        summary=state.get("summary", "Workflow did not complete."),
        proposed_action=state.get("proposed_action"),
        approval_required=True,
        attempts=state.get("attempts", 0),
        errors=state.get("errors", [])
    )
    return outcome, elapsed
