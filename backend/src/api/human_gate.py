from fastapi import APIRouter, Body, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional
from src.agents.workflows.rfq.agents.human_gate_agent import HumanGateAgent
from src.agents.workflows.rfq.models import ApprovalDecision, ApprovalGateResponse
from src.agents.workflows.rfq.orchestrators.rfq_workflow_orchestrator import RFQWorkflowOrchestrator
from src.persistence.threads import get_thread_repository
from src.persistence.models import Message
from datetime import datetime
import json
import logging
from src.agents.workflows.rfq.rfq_section_builder import (
    build_phase_block,
    build_purchase_order_markdown,
    prune_phase_blocks,
)

router = APIRouter(prefix="/api/human-gate", tags=["HumanGate"])
human_gate_agent = HumanGateAgent()
logger = logging.getLogger(__name__)

@router.post("/action", name="human_gate_action")
async def human_gate_action(
    action: str = Body(..., embed=True),
    data: Optional[dict] = Body(None, embed=True),
    thread_id: Optional[str] = Body(None, embed=True)
):
    """
    Receives human gate action from frontend and resumes workflow.
    action: 'approve', 'edit', or 'reject'
    data: optional dict for edits (e.g., {suggested_unit_price: 100.0})
    thread_id: thread ID to load workflow state from
    """
    try:
        # Load workflow state from thread if provided
        workflow_state = None
        thread = None
        if thread_id:
            thread_repo = get_thread_repository()
            thread = await thread_repo.get(thread_id, "rfq-procurement")
            if thread and thread.workflow_state:
                workflow_state = thread.workflow_state
        
        if not workflow_state:
            raise HTTPException(status_code=400, detail="No workflow state found for resumption")
        
        # Create approval response based on action
        if action == "approve":
            decision = ApprovalDecision.APPROVED
        elif action == "reject":
            decision = ApprovalDecision.REJECTED  
        else:
            decision = ApprovalDecision.MORE_INFO
        
        # Create approval response
        approval_response = ApprovalGateResponse(
            request_id=workflow_state.get("workflow_id", "unknown"),
            decision=decision,
            decision_maker="User",
            justification=f"Decision: {action}"
        )
        
        # Store approval decision message in thread
        approval_message = f"""## Phase 6: Approval Decision

✅ **{decision.value.title()}** by User

**Decision:** {action.title()}
**Justification:** {approval_response.justification}
"""
        
        approval_msg = Message(
            id=f"msg_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_approval",
            role="assistant",
            content=approval_message,
            timestamp=datetime.utcnow(),
        )
        await thread_repo.add_message(thread_id, "rfq-procurement", approval_msg, thread)
        
        # Clear workflow state and resume if approved
        if decision == ApprovalDecision.APPROVED:
            # Continue workflow from Phase 7 with the approval
            orchestrator = RFQWorkflowOrchestrator(thread_id=thread_id)
            
            # We need to continue the workflow from Phase 7
            # For now, return a continuation signal
            thread.workflow_state = {
                **workflow_state,
                "approval_response": approval_response.model_dump(),
                "phase": "phase7_continue"
            }
            await thread_repo.update(thread)
            
            return {
                "result": "approved",
                "approval_response": approval_response.model_dump(),
                "status": "approved_continue_workflow",
                "message": "Approval completed. Workflow will continue with purchase order generation."
            }
        else:
            # Clear workflow state for rejection
            thread.workflow_state = None
            await thread_repo.update(thread)
            
            return {
                "result": "rejected" if decision == ApprovalDecision.REJECTED else "info_requested",
                "approval_response": approval_response.model_dump(),
                "status": "workflow_terminated",
                "message": f"Workflow {action}ed. No further action needed."
            }
        
    except Exception as e:
        logger.error(f"Error handling human gate action: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process approval: {str(e)}")


@router.post("/resume", name="human_gate_resume")
async def human_gate_resume(
    thread_id: str = Body(..., embed=True)
):
    """Resume RFQ workflow after approval (Phase 7+). Emits purchase order generation phase block.

    Frontend should call after receiving status 'approved_continue_workflow'.
    """
    try:
        thread_repo = get_thread_repository()
        thread = await thread_repo.get(thread_id, "rfq-procurement")
        if not thread or not thread.workflow_state:
            raise HTTPException(status_code=400, detail="No resumable workflow state found")
        state = thread.workflow_state
        if state.get("phase") != "phase7_continue":
            raise HTTPException(status_code=400, detail="Workflow state not in resumable phase")

        # Extract needed objects
        comparison_report_data = state.get("comparison_report")
        negotiation_recommendation_data = state.get("negotiation_recommendation")
        requirements_data = state.get("requirements")
        workflow_id = state.get("workflow_id", thread_id)

        if not (comparison_report_data and negotiation_recommendation_data and requirements_data):
            raise HTTPException(status_code=400, detail="Incomplete workflow state for resumption")

        # Rehydrate minimal objects (avoid full model complexity; rely on dict fields used for PO)
        from datetime import timedelta
        from datetime import datetime as dt
        from src.agents.workflows.rfq.models import PurchaseOrder
        # Determine target vendor from negotiation recommendation
        target_vendor_id = negotiation_recommendation_data.get("vendor_id")
        target_vendor_name = negotiation_recommendation_data.get("vendor_name")
        unit_price = negotiation_recommendation_data.get("suggested_unit_price") or 0
        quantity = requirements_data.get("quantity", 0)
        total_amount = unit_price * quantity
        delivery_date = negotiation_recommendation_data.get("suggested_delivery_date") or dt.utcnow() + timedelta(days=14)
        payment_terms = negotiation_recommendation_data.get("suggested_payment_terms") or "Net 30"

        po = PurchaseOrder(
            po_number=f"PO-{workflow_id[-8:]}",
            po_date=dt.utcnow(),
            vendor_id=target_vendor_id,
            vendor_name=target_vendor_name,
            vendor_contact="procurement@vendor.example.com",
            buyer_name=state.get("buyer_name", "Buyer"),
            buyer_email=state.get("buyer_email", "buyer@example.com"),
            product_id=requirements_data.get("product_id", "unknown"),
            product_name=requirements_data.get("product_name", "Product"),
            quantity=quantity,
            unit="pieces",
            unit_price=unit_price,
            total_amount=total_amount,
            delivery_date=delivery_date,
            payment_terms=payment_terms,
        )

        # Build structured markdown sections for PO (Phase 7)
        po_sections = build_purchase_order_markdown(po)
        po_block = build_phase_block(
            phase_id="phase7_complete",
            title="Phase 7: Purchase Order",
            markdown_sections=po_sections,
            metrics={
                "duration_ms": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "estimated": True,
            },
            sub_blocks=[{
                "id": "signoff",
                "title": "Sign-Off",
                "markdown": "Authorized Buyer: ______________________  Date: __________\nVendor Rep: ________________________  Date: __________"
            }]
        )

        markdown = po_block["markdown"]

        # Persist phase block (with pruning)
        if thread.metadata is None:
            thread.metadata = {}
        blocks = thread.metadata.get("rfq_phases", [])
        blocks.append(po_block)
        blocks = prune_phase_blocks(blocks, max_blocks=8)
        thread.metadata["rfq_phases"] = blocks

        # Clear workflow_state (workflow finished)
        thread.workflow_state = None
        await thread_repo.update(thread)

        return {
            "status": "phase7_complete",
            "purchase_order": po.model_dump(),
            "markdown": markdown,
            "message": "Purchase order generated successfully.",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resuming workflow: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to resume workflow: {str(e)}")
