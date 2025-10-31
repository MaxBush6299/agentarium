from fastapi import APIRouter, Body
from typing import Optional
from src.agents.workflows.rfq.agents.human_gate_agent import HumanGateAgent

router = APIRouter(prefix="/api/human-gate", tags=["HumanGate"])
human_gate_agent = HumanGateAgent()

@router.post("/action", name="human_gate_action")
async def human_gate_action(
    action: str = Body(..., embed=True),
    data: Optional[dict] = Body(None, embed=True)
):
    """
    Receives human gate action from frontend and resumes workflow.
    action: 'approve', 'edit', or 'reject'
    data: optional dict for edits (e.g., {suggested_unit_price: 100.0})
    """
    result = await human_gate_agent.handle_human_action(action, data)
    return {"result": result}
