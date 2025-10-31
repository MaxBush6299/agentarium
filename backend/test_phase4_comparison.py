"""
Test Phase 4: Comparison & Analysis Agent
"""

import pytest
import asyncio
from datetime import datetime, timedelta

from src.agents.workflows.rfq.agents.comparison_analysis_agent import ComparisonAndAnalysisAgent
from src.agents.workflows.rfq.models import VendorProfile, QuoteResponse


@pytest.mark.asyncio
async def test_comparison_agent_initialization():
    """Test that comparison agent initializes correctly."""
    agent = ComparisonAndAnalysisAgent()
    assert agent.name == "Comparison & Analysis Agent"
    assert agent.model == "gpt-4o"


@pytest.mark.asyncio
async def test_merge_evaluation_tracks():
    """Test merging of three evaluation tracks with equal weighting."""
    agent = ComparisonAndAnalysisAgent()
    
    # Create mock vendors
    vendors = [
        VendorProfile(
            vendor_id="vendor-1",
            vendor_name="AccuParts",
            contact_email="sales@accuparts.com",
            contact_phone="+1-555-0101",
            country="USA",
        ),
        VendorProfile(
            vendor_id="vendor-2",
            vendor_name="EuroComponent",
            contact_email="sales@eurocomp.de",
            contact_phone="+49-123-456789",
            country="Germany",
        ),
        VendorProfile(
            vendor_id="vendor-3",
            vendor_name="QualitySupply",
            contact_email="info@qualitysupply.co.uk",
            contact_phone="+44-1234-567890",
            country="UK",
        ),
    ]
    
    # Create mock evaluations: each track gives confidence 0-1
    compliance_evals = {
        "vendor-1": {"confidence": 0.90, "risk_level": "LOW"},
        "vendor-2": {"confidence": 0.85, "risk_level": "MEDIUM"},
        "vendor-3": {"confidence": 0.75, "risk_level": "MEDIUM"},
    }
    
    delivery_evals = {
        "vendor-1": {"confidence": 0.88, "risk_level": "LOW"},
        "vendor-2": {"confidence": 0.82, "risk_level": "MEDIUM"},
        "vendor-3": {"confidence": 0.80, "risk_level": "MEDIUM"},
    }
    
    financial_evals = {
        "vendor-1": {"confidence": 0.85, "risk_level": "LOW"},
        "vendor-2": {"confidence": 0.88, "risk_level": "LOW"},
        "vendor-3": {"confidence": 0.70, "risk_level": "HIGH"},
    }
    
    # Merge tracks
    merged_scores = await agent.merge_evaluation_tracks(
        vendors=vendors,
        compliance_evaluations=compliance_evals,
        delivery_evaluations=delivery_evals,
        financial_evaluations=financial_evals,
    )
    
    # Verify results
    assert len(merged_scores) == 3
    assert "vendor-1" in merged_scores
    assert "vendor-2" in merged_scores
    assert "vendor-3" in merged_scores
    
    # Vendor 1 should have highest score: (90 + 88 + 85) / 3 = 87.67
    expected_v1 = (90 + 88 + 85) / 3
    assert abs(merged_scores["vendor-1"] - expected_v1) < 0.1
    
    # Vendor 2 should be middle: (85 + 82 + 88) / 3 = 85.0
    expected_v2 = (85 + 82 + 88) / 3
    assert abs(merged_scores["vendor-2"] - expected_v2) < 0.1
    
    # Vendor 3 should be lowest: (75 + 80 + 70) / 3 = 75.0
    expected_v3 = (75 + 80 + 70) / 3
    assert abs(merged_scores["vendor-3"] - expected_v3) < 0.1
    
    print("✓ Score merging working correctly with equal weighting")


@pytest.mark.asyncio
async def test_full_comparison_analysis():
    """Test full vendor comparison and analysis."""
    agent = ComparisonAndAnalysisAgent()
    
    # Create mock vendors
    vendors = [
        VendorProfile(
            vendor_id="vendor-1",
            vendor_name="AccuParts",
            contact_email="sales@accuparts.com",
            contact_phone="+1-555-0101",
            country="USA",
        ),
        VendorProfile(
            vendor_id="vendor-2",
            vendor_name="EuroComponent",
            contact_email="sales@eurocomp.de",
            contact_phone="+49-123-456789",
            country="Germany",
        ),
    ]
    
    # Create mock quotes with required fields
    delivery_date_1 = datetime.now() + timedelta(days=14)
    delivery_date_2 = datetime.now() + timedelta(days=21)
    
    quotes = [
        QuoteResponse(
            quote_id="quote-1",
            submission_id="sub-1",
            vendor_id="vendor-1",
            vendor_name="AccuParts",
            unit_price=15.50,
            total_price=1550.00,
            delivery_date=delivery_date_1,
            delivery_lead_days=14,
        ),
        QuoteResponse(
            quote_id="quote-2",
            submission_id="sub-2",
            vendor_id="vendor-2",
            vendor_name="EuroComponent",
            unit_price=16.00,
            total_price=1600.00,
            delivery_date=delivery_date_2,
            delivery_lead_days=21,
        ),
    ]
    
    # Create mock evaluations
    compliance_evals = {
        "vendor-1": {"confidence": 0.90, "risk_level": "LOW"},
        "vendor-2": {"confidence": 0.85, "risk_level": "MEDIUM"},
    }
    
    delivery_evals = {
        "vendor-1": {"confidence": 0.88, "risk_level": "LOW"},
        "vendor-2": {"confidence": 0.82, "risk_level": "MEDIUM"},
    }
    
    financial_evals = {
        "vendor-1": {"confidence": 0.85, "risk_level": "LOW"},
        "vendor-2": {"confidence": 0.88, "risk_level": "LOW"},
    }
    
    # Run analysis
    report = await agent.analyze_vendors(
        vendors=vendors,
        quotes=quotes,
        compliance_evaluations=compliance_evals,
        delivery_evaluations=delivery_evals,
        financial_evaluations=financial_evals,
    )
    
    # Verify report structure
    assert report is not None
    assert len(report.normalized_quotes) == 2
    assert len(report.top_ranked_vendors) == 2
    
    # Verify top vendor is AccuParts (highest score)
    assert report.top_ranked_vendors[0]["vendor_name"] == "AccuParts"
    assert report.top_ranked_vendors[0]["recommendation"] == "RECOMMENDED"
    
    # Verify EuroComponent is second
    assert report.top_ranked_vendors[1]["vendor_name"] == "EuroComponent"
    assert report.top_ranked_vendors[1]["recommendation"] == "ACCEPTABLE"
    
    # Verify recommendations include top vendor
    assert "AccuParts" in report.recommendations
    
    print("✓ Full comparison analysis working correctly")
    print(f"✓ Report ID: {report.report_id}")
    print(f"✓ Top vendor: {report.top_ranked_vendors[0]['vendor_name']} "
          f"(Score: {report.top_ranked_vendors[0]['score']:.1f}/5.0)")


if __name__ == "__main__":
    # Run tests
    asyncio.run(test_comparison_agent_initialization())
    asyncio.run(test_merge_evaluation_tracks())
    asyncio.run(test_full_comparison_analysis())
    print("\n✅ All Phase 4 tests passed!")
