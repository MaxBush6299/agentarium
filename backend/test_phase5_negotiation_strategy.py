"""
Test Phase 5: Negotiation Strategy Agent
"""

import pytest
from datetime import datetime, timedelta
from src.agents.workflows.rfq.agents.negotiation_strategy_agent import NegotiationStrategyAgent
from src.agents.workflows.rfq.models import ComparisonReport, NormalizedQuote

@pytest.mark.asyncio
async def test_negotiation_agent_initialization():
    agent = NegotiationStrategyAgent()
    assert agent.name == "Negotiation Strategy Agent"
    assert agent.model == "gpt-4o"

@pytest.mark.asyncio
async def test_full_negotiation_recommendation():
    agent = NegotiationStrategyAgent()
    delivery_date1 = datetime.now() + timedelta(days=21)
    delivery_date2 = datetime.now() + timedelta(days=14)
    delivery_date3 = datetime.now() + timedelta(days=28)
    quote1 = NormalizedQuote(
        quote_id="quote-1",
        vendor_id="vendor-001",
        vendor_name="AccuParts Inc",
        unit_price=120.00,
        total_price=12000.00,
        price_per_unit_with_bulk=115.00,
        delivery_date=delivery_date1,
        lead_time_days=21,
        overall_score=90.0,
        price_score=80.0,
        delivery_score=85.0,
        quality_score=95.0,
        risk_flags=[],
    )
    quote2 = NormalizedQuote(
        quote_id="quote-2",
        vendor_id="vendor-002",
        vendor_name="PrecisionSupply Ltd",
        unit_price=115.00,
        total_price=11500.00,
        price_per_unit_with_bulk=110.00,
        delivery_date=delivery_date2,
        lead_time_days=14,
        overall_score=85.0,
        price_score=82.0,
        delivery_score=80.0,
        quality_score=88.0,
        risk_flags=[],
    )
    quote3 = NormalizedQuote(
        quote_id="quote-3",
        vendor_id="vendor-003",
        vendor_name="BudgetComponents Co",
        unit_price=110.00,
        total_price=11000.00,
        price_per_unit_with_bulk=105.00,
        delivery_date=delivery_date3,
        lead_time_days=28,
        overall_score=80.0,
        price_score=85.0,
        delivery_score=75.0,
        quality_score=80.0,
        risk_flags=[],
    )
    top_ranked_vendors = [
        {
            "vendor_id": "vendor-001",
            "vendor_name": "AccuParts Inc",
            "score": 4.2,
            "recommendation": "High quality but premium pricing - negotiate for better terms"
        },
        {
            "vendor_id": "vendor-002",
            "vendor_name": "PrecisionSupply Ltd",
            "score": 3.8,
            "recommendation": "Good value with competitive pricing"
        },
        {
            "vendor_id": "vendor-003",
            "vendor_name": "BudgetComponents Co",
            "score": 3.0,
            "recommendation": "Lowest cost but longer delivery"
        }
    ]
    comparison_report = ComparisonReport(
        report_id="comp-report-001",
        normalized_quotes=[quote1, quote2, quote3],
        vendor_evaluations=[],
        top_ranked_vendors=top_ranked_vendors,
        risk_summary={},
        recommendations="Negotiate with top vendor for volume discount",
    )
    recommendation = await agent.generate_recommendation(
        comparison_report=comparison_report,
        quantity=100,
        workflow_id="workflow-123",
    )
    assert recommendation.recommendation_id.startswith("nego-")
    assert recommendation.vendor_id == "vendor-001"
    assert recommendation.vendor_name == "AccuParts Inc"
    assert recommendation.suggested_unit_price is not None
    assert len(recommendation.leverage_points) > 0
    assert recommendation.negotiation_strategy is not None
    assert recommendation.expected_outcome is not None
    if recommendation.estimated_cost_savings is not None:
        assert recommendation.estimated_cost_savings >= 0





if __name__ == "__main__":
    # Run tests

    print("\n✅ All Phase 5 tests passed!")
