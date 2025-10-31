"""
Phase 8 Integration Test: End-to-End RFQ Workflow

Tests the complete workflow from RFQ request to PO generation:
1. Phase 2: Preprocessing (ProductReview + VendorQualification)
2. Phase 3: Parallel Orchestration (Submission + Parsing + 3 Evaluation Tracks)
3. Phase 4: Comparison & Analysis
4. Phase 5: Negotiation Strategy
5. Phase 6: Human Gate (auto-approved for testing)
6. Phase 7: Purchase Order Generation

This test validates the entire pipeline works end-to-end.
"""

import pytest
from src.agents.workflows.rfq.models import ApprovalDecision
import asyncio
import time
from datetime import datetime, timedelta

from src.agents.workflows.rfq.models import RFQRequest
from src.agents.workflows.rfq.orchestrators.rfq_workflow_orchestrator import (
    RFQWorkflowOrchestrator,
)
from src.agents.workflows.rfq.observability import rfq_logger


@pytest.mark.asyncio
async def test_full_workflow_orchestrator_initialization():
    """Test that the master orchestrator initializes correctly."""
    orchestrator = RFQWorkflowOrchestrator()
    
    # Verify all sub-components are initialized
    assert orchestrator.preprocessing_orchestrator is not None
    assert orchestrator.parallel_evaluation_orchestrator is not None
    assert orchestrator.rfq_submission_executor is not None
    assert orchestrator.quote_parsing_executor is not None
    assert orchestrator.comparison_agent is not None
    assert orchestrator.negotiation_agent is not None
    assert orchestrator.human_gate_agent is not None
    assert orchestrator.po_agent is not None
    
    rfq_logger.info("✓ Master orchestrator initialization test passed")


@pytest.mark.asyncio
async def test_end_to_end_workflow_with_auto_approval():
    """
    Test complete RFQ workflow from request to PO generation.
    
    This test executes all 6 phases in sequence and validates:
    - Each phase produces expected outputs
    - Data flows correctly between phases
    - Final PO is generated with correct details
    - All phases complete within reasonable time
    """
    
    workflow_id = f"test-e2e-{int(time.time())}"
    rfq_logger.info(
        f"Starting end-to-end workflow test",
        extra={"workflow_id": workflow_id},
    )
    
    start_time = time.time()
    
    # Create test RFQ request
    rfq_request = RFQRequest(
        request_id=f"REQ-{workflow_id}",
        requestor_name="Test Procurement Manager",
        requestor_email="test.procurement@company.com",
        product_id="SENSOR-E2E-001",
        product_name="High-Precision Industrial Sensors",
        category="industrial_sensors",
        quantity=1000,
        unit="pieces",
        required_certifications=["IP67", "UL508", "CE"],
        special_requirements="3-year warranty, priority delivery, quality inspection required",
        desired_delivery_date=datetime.now() + timedelta(weeks=10),
        max_lead_time_days=70,
        budget_amount=250000,
    )
    
    # Initialize orchestrator
    orchestrator = RFQWorkflowOrchestrator()
    
    # Execute full workflow with auto-approval
    results = await orchestrator.execute_full_workflow(
        rfq_request=rfq_request,
        workflow_id=workflow_id,
        buyer_name="Test Procurement Manager",
        buyer_email="test.procurement@company.com",
        wait_for_human=False,  # Auto-approve for testing
    )
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    # =======================================================================
    # VALIDATE RESULTS
    # =======================================================================
    
    # Overall workflow status
    assert results["status"] == "completed", f"Expected 'completed', got '{results['status']}'"
    assert results["workflow_id"] == workflow_id
    assert results["request_id"] == rfq_request.request_id
    
    rfq_logger.info(f"✓ Workflow status: {results['status']}")
    
    # Phase 2: Preprocessing
    assert "phase2_requirements" in results
    assert "phase2_vendors" in results
    
    requirements = results["phase2_requirements"]
    vendors = results["phase2_vendors"]
    
    assert requirements.product_name == rfq_request.product_name
    assert requirements.quantity == rfq_request.quantity
    assert len(vendors) > 0, "No vendors qualified"
    
    rfq_logger.info(f"✓ Phase 2: {len(vendors)} vendors qualified")
    
    # Phase 3: Parallel Orchestration
    assert "phase3_raw_quotes" in results
    assert "phase3_parsed_quotes" in results
    assert "phase3_evaluations" in results
    
    raw_quotes = results["phase3_raw_quotes"]
    parsed_quotes = results["phase3_parsed_quotes"]
    vendor_evaluations = results["phase3_evaluations"]  # List of VendorEvaluation dicts
    track_results = results["phase3_track_results"]  # List of track-level evaluation results
    
    assert len(raw_quotes) > 0, "No raw quotes received"
    assert len(parsed_quotes) > 0, "No parsed quotes available"
    assert len(vendor_evaluations) > 0, "No vendor evaluations"
    assert len(track_results) > 0, "No track results"
    
    # Verify we have compliance, delivery, and financial tracks
    track_names = {t["track_name"] for t in track_results}
    assert "Compliance" in track_names, "Missing compliance track"
    assert "Delivery" in track_names, "Missing delivery track"
    assert "Financial" in track_names, "Missing financial track"
    
    rfq_logger.info(f"✓ Phase 3: {len(parsed_quotes)} quotes evaluated across 3 tracks")
    
    # Phase 4: Comparison & Analysis
    assert "phase4_comparison_report" in results
    
    comparison_report_dict = results["phase4_comparison_report"]
    
    assert "report_id" in comparison_report_dict
    assert len(comparison_report_dict["top_ranked_vendors"]) > 0, "No vendors ranked"
    assert len(comparison_report_dict["normalized_quotes"]) > 0, "No normalized quotes"
    
    top_vendor = comparison_report_dict["top_ranked_vendors"][0]
    rfq_logger.info(f"✓ Phase 4: Top vendor is {top_vendor['vendor_name']} with score {top_vendor['score']}")
    
    # Phase 5: Negotiation Strategy
    assert "phase5_negotiation_recommendation" in results
    
    negotiation_recommendation_dict = results["phase5_negotiation_recommendation"]
    
    assert negotiation_recommendation_dict["recommendation_id"].startswith("nego-")
    assert negotiation_recommendation_dict["vendor_id"] is not None
    assert negotiation_recommendation_dict["vendor_name"] is not None
    assert negotiation_recommendation_dict["suggested_unit_price"] > 0
    assert negotiation_recommendation_dict["estimated_cost_savings"] >= 0
    
    rfq_logger.info(
        f"✓ Phase 5: Target vendor {negotiation_recommendation_dict['vendor_name']}, "
        f"suggested price ${negotiation_recommendation_dict['suggested_unit_price']:.2f}, "
        f"estimated savings ${negotiation_recommendation_dict['estimated_cost_savings']:.2f}"
    )
    
    # Phase 6: Human Gate
    assert "phase6_approval" in results
    
    approval_dict = results["phase6_approval"]
    
    assert approval_dict["decision"] == ApprovalDecision.APPROVED
    assert approval_dict["decision_maker"] == "Test Procurement Manager"
    
    rfq_logger.info(f"✓ Phase 6: Approval received from {approval_dict['decision_maker']}")
    
    # Phase 7: Purchase Order
    assert "phase7_purchase_order" in results
    assert "final_purchase_order" in results
    
    purchase_order_dict = results["final_purchase_order"]
    
    assert purchase_order_dict["po_number"].startswith("PO-")
    assert purchase_order_dict["vendor_id"] == negotiation_recommendation_dict["vendor_id"]
    assert purchase_order_dict["product_name"] == rfq_request.product_name
    assert purchase_order_dict["quantity"] == rfq_request.quantity
    assert purchase_order_dict["unit_price"] > 0
    assert purchase_order_dict["total_amount"] > 0
    assert purchase_order_dict["status"] == "issued"
    
    rfq_logger.info(
        f"✓ Phase 7: PO {purchase_order_dict['po_number']} issued for "
        f"{purchase_order_dict['quantity']} units at ${purchase_order_dict['unit_price']:.2f}/unit, "
        f"total ${purchase_order_dict['total_amount']:.2f}"
    )
    
    # Performance validation
    rfq_logger.info(f"✓ Total execution time: {execution_time:.2f}s")
    
    # The workflow should complete in reasonable time
    # Allow up to 30s for full workflow with real LLM calls
    assert execution_time < 30.0, f"Workflow took too long: {execution_time:.2f}s"
    
    print("\n" + "=" * 80)
    print("END-TO-END WORKFLOW TEST SUMMARY")
    print("=" * 80)
    print(f"Workflow ID: {workflow_id}")
    print(f"Status: {results['status']}")
    print(f"Execution Time: {execution_time:.2f}s")
    print(f"\nPhase 2: {len(vendors)} vendors qualified")
    print(f"Phase 3: {len(parsed_quotes)} quotes evaluated")
    print(f"Phase 4: Top vendor - {top_vendor['vendor_name']}")
    print(f"Phase 5: Target vendor - {negotiation_recommendation_dict['vendor_name']}")
    print(f"Phase 6: Approval - {approval_dict['decision']}")
    print(f"Phase 7: PO {purchase_order_dict['po_number']} issued")
    print(f"\n✅ All phases completed successfully!")
    print("=" * 80)


@pytest.mark.asyncio
async def test_workflow_with_human_approval_pending():
    """
    Test workflow that pauses at human gate.
    
    This test validates that the workflow correctly pauses when
    wait_for_human=True and returns awaiting_approval status.
    """
    
    workflow_id = f"test-pending-{int(time.time())}"
    
    rfq_request = RFQRequest(
        request_id=f"REQ-{workflow_id}",
        requestor_name="Test Manager",
        requestor_email="test@company.com",
        product_id="SENSOR-PENDING-001",
        product_name="Test Sensors",
        category="industrial_sensors",
        quantity=500,
        unit="pieces",
        required_certifications=["IP67"],
        special_requirements="Standard warranty",
        desired_delivery_date=datetime.now() + timedelta(weeks=8),
        max_lead_time_days=56,
        budget_amount=100000,
    )
    
    orchestrator = RFQWorkflowOrchestrator()
    
    # Execute with wait_for_human=True
    results = await orchestrator.execute_full_workflow(
        rfq_request=rfq_request,
        workflow_id=workflow_id,
        buyer_name="Test Manager",
        buyer_email="test@company.com",
        wait_for_human=True,  # Should pause at Phase 6
    )
    
    # Validate workflow paused at human gate
    assert results["status"] == "awaiting_approval"
    assert "message" in results
    assert results["message"] == "Workflow paused for human approval"
    
    # Should have completed Phases 2-5
    assert "phase2_requirements" in results
    assert "phase3_parsed_quotes" in results
    assert "phase4_comparison_report" in results
    assert "phase5_negotiation_recommendation" in results
    assert "phase6_human_gate_request" in results
    
    # Should NOT have Phase 7 yet
    assert "phase7_purchase_order" not in results
    assert "final_purchase_order" not in results
    
    rfq_logger.info(
        f"✓ Workflow correctly paused at Phase 6 with status: {results['status']}"
    )
    
    print("\n✅ Human gate pending test passed - workflow correctly pauses for approval")


if __name__ == "__main__":
    # Run tests
    asyncio.run(test_full_workflow_orchestrator_initialization())
    asyncio.run(test_end_to_end_workflow_with_auto_approval())
    asyncio.run(test_workflow_with_human_approval_pending())
