from app.schemas import ToolResult

TICKETS = {"T-100": "open", "T-200": "pending", "T-300": "closed"}

class MockSupportAPI:
    def __init__(self):
        self.calls = {}

    def get_ticket(self, ticket_id: str, scenario: str) -> ToolResult:
        self.calls[ticket_id] = self.calls.get(ticket_id, 0) + 1
        call = self.calls[ticket_id]
        if scenario == "timeout_always" or (scenario == "timeout_once" and call == 1):
            return ToolResult(ok=False, ticket_id=ticket_id, error="timeout", retryable=True)
        if scenario == "malformed":
            return ToolResult(ok=False, ticket_id=ticket_id, error="malformed_response", retryable=False)
        if ticket_id not in TICKETS:
            return ToolResult(ok=False, ticket_id=ticket_id, error="not_found", retryable=False)
        return ToolResult(ok=True, ticket_id=ticket_id, status=TICKETS[ticket_id])
