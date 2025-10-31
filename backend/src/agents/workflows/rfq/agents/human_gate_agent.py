"""
Phase 6: HumanGateAgent for RFQ Workflow
This agent pauses the workflow for human review and input before finalizing negotiation recommendations.
Inspired by: https://github.com/microsoft/agent-framework/blob/main/python/samples/getting_started/workflows/human-in-the-loop/guessing_game_with_human_input.py
"""
import asyncio
from typing import Any, Optional

class HumanGateAgent:
    def __init__(self, name: str = "Human Gate Agent"):
        self.name = name
        self.pending_request: Optional[dict] = None

    async def request_human_input(self, recommendation: Any) -> Any:
        # Store pending request for frontend polling
        self.pending_request = {
            "recommendation": recommendation,
            "status": "pending",
            "action": None,
        }
        # Return a special message to frontend to trigger human gate UI
        return {
            "type": "human_gate",
            "recommendation": recommendation,
            "actions": ["approve", "edit", "reject"],
        }

    async def handle_human_action(self, action: str, data: Optional[dict] = None) -> Any:
        if not self.pending_request:
            return None
        recommendation = self.pending_request["recommendation"]
        self.pending_request["action"] = action
        self.pending_request["status"] = "completed"
        if action == "approve":
            return recommendation
        elif action == "edit":
            # For demo: allow editing a field (e.g., suggested_unit_price)
            if data and "suggested_unit_price" in data:
                try:
                    recommendation.suggested_unit_price = float(data["suggested_unit_price"])
                except Exception:
                    pass
            return recommendation
        elif action == "reject":
            return None
        else:
            return recommendation
