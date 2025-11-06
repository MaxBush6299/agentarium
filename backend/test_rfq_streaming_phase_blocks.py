import asyncio
import pytest
from datetime import datetime

from src.agents.workflows.rfq.models import RFQRequest
from src.agents.workflows.rfq.orchestrators.rfq_workflow_orchestrator import RFQWorkflowOrchestrator
from src.persistence.threads import get_thread_repository
from src.persistence.models import Thread


@pytest.mark.asyncio
async def test_rfq_streaming_produces_phase_blocks():
    repo = get_thread_repository()
    thread_id = f"thread_test_{datetime.utcnow().strftime('%H%M%S')}"

    # Create thread beforehand with stable agentId
    thread = Thread(
        id=thread_id,
        agentId="rfq-procurement",
        workflowId="wf-test",
        title="RFQ Test Thread",
        messages=[],
        runs=[],
        status="active",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    await repo.container.create_item(body=thread.model_dump(by_alias=True))

    rfq_request = RFQRequest(
        request_id="rfq-test-1",
        product_id="PROD-1",
        product_name="Test Widgets",
        category="widgets",
        quantity=10,
        unit="pieces",
        required_certifications=["ISO-9001"],
        special_requirements="None",
        desired_delivery_date=datetime.utcnow(),
        max_lead_time_days=30,
        budget_amount=1000.0,
        requestor_name="Tester",
        requestor_email="tester@example.com",
    )

    orchestrator = RFQWorkflowOrchestrator(thread_id=thread_id, agent_id="rfq-procurement")

    phases = []
    async for event in orchestrator.execute_full_workflow_streaming(
        rfq_request=rfq_request,
        workflow_id="wf-test-run",
        buyer_name=rfq_request.requestor_name,
        buyer_email=rfq_request.requestor_email,
        wait_for_human=False,  # auto-approve to finish all phases
    ):
        if event.get("type") == "agent_section":
            phases.append(event)

    # Ensure we captured expected phase blocks (phase2..phase7 when auto-approved)
    phase_ids = {p["phase"] for p in phases}
    assert "phase2_complete" in phase_ids
    assert "phase3_complete" in phase_ids
    assert "phase4_complete" in phase_ids
    assert "phase5_complete" in phase_ids
    assert "phase6_complete" in phase_ids  # auto-approved path
    assert "phase7_complete" in phase_ids

    # Verify thread metadata persistence
    stored_thread = await repo.get(thread_id, "rfq-procurement")
    assert stored_thread is not None
    assert stored_thread.metadata is not None
    blocks = stored_thread.metadata.get("rfq_phases")
    assert blocks is not None
    # Should have at most 8 and at least the phases we ran
    assert len(blocks) >= 6
    assert any(b["phase_id"] == "phase4_complete" for b in blocks)

    # Metrics sanity: duration_ms present, token counts are ints
    sample = blocks[0]
    m = sample["metrics"]
    assert "duration_ms" in m and isinstance(m["duration_ms"], int)
    assert all(isinstance(m[k], int) for k in ["prompt_tokens", "completion_tokens", "total_tokens"])
