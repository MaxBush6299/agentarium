"""
Phase 6 Integration Test: Verifies HumanGateAgent workflow
"""
import pytest
from datetime import datetime, timedelta
from src.agents.workflows.rfq.agents.phase6_negotiation_orchestrator import Phase6NegotiationOrchestrator
from src.agents.workflows.rfq.models import ComparisonReport, NormalizedQuote

@pytest.mark.asyncio
async def test_phase6_human_gate_workflow(monkeypatch):
    orchestrator = Phase6NegotiationOrchestrator()
    delivery_date = datetime.now() + timedelta(days=14)
    quote = NormalizedQuote(
        quote_id="quote-1",
        vendor_id="vendor-001",
        vendor_name="AccuParts Inc",
        unit_price=120.00,
        total_price=12000.00,
        price_per_unit_with_bulk=115.00,
        delivery_date=delivery_date,
        lead_time_days=14,
        overall_score=90.0,
        price_score=80.0,
        delivery_score=85.0,
        quality_score=95.0,
        risk_flags=[],
    )
    top_ranked_vendors = [
        {
            "vendor_id": "vendor-001",
            "vendor_name": "AccuParts Inc",
            "score": 4.2,
            "recommendation": "High quality but premium pricing - negotiate for better terms"
        }
    ]
    comparison_report = ComparisonReport(
        report_id="comp-report-001",
        normalized_quotes=[quote],
        vendor_evaluations=[],
        top_ranked_vendors=top_ranked_vendors,
        risk_summary={},
        recommendations="Negotiate with top vendor for volume discount",
    )
    # Simulate human approval
    monkeypatch.setattr('builtins.input', lambda _: 'approve')
    result = await orchestrator.run(comparison_report, quantity=100, workflow_id="workflow-123")
    assert result is not None
    assert result.vendor_id == "vendor-001"
    assert result.vendor_name == "AccuParts Inc"
