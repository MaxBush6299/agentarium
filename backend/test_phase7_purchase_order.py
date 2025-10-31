"""
Phase 7 Integration Test: Purchase Order Generation

Tests the PurchaseOrderAgent with approved negotiation recommendations.
"""

import pytest
from datetime import datetime, timedelta
from src.agents.workflows.rfq.agents.purchase_order_agent import PurchaseOrderAgent
from src.agents.workflows.rfq.models import (
    NegotiationRecommendation,
    ApprovalGateResponse,
    ApprovalDecision,
    ProductRequirements,
    VendorProfile,
)


@pytest.mark.asyncio
async def test_po_agent_initialization():
    """Test PO agent initializes correctly."""
    agent = PurchaseOrderAgent()
    assert agent.name == "Purchase Order Agent"
    print("✓ PO agent initialized")


@pytest.mark.asyncio
async def test_generate_purchase_order():
    """Test PO generation from approved recommendation."""
    agent = PurchaseOrderAgent()
    
    # Create product requirements
    requirements = ProductRequirements(
        product_id="prod-001",
        product_name="Industrial Sensor XYZ-100",
        category="electronics",
        quantity=100,
        unit="pieces",
        specifications={"voltage": "24V", "accuracy": "±0.1%"},
        required_certifications=["CE", "UL", "ISO 9001"],
        compliance_standards=["RoHS", "REACH"],
        desired_delivery_date=datetime.now() + timedelta(days=21),
        max_lead_time_days=30,
    )
    
    # Create vendor profile
    vendor = VendorProfile(
        vendor_id="vendor-001",
        vendor_name="AccuParts Inc",
        country="USA",
        certifications=["CE", "UL", "ISO 9001", "ISO 14001"],
        rating=4.7,
        contact_email="sales@accuparts.com",
        contact_phone="+1-555-0100",
        min_order_quantity=50,
        distance_miles=2000,
    )
    
    # Create negotiation recommendation
    recommendation = NegotiationRecommendation(
        recommendation_id="nego-001",
        vendor_id="vendor-001",
        vendor_name="AccuParts Inc",
        current_unit_price=120.00,
        suggested_unit_price=110.00,
        leverage_points=[
            "Bulk volume commitment (100 units)",
            "Long-term partnership potential",
            "Competitor pricing lower by 8%",
        ],
        negotiation_strategy="Emphasize volume commitment and request 8% discount to match market rates",
        expected_outcome="Target: $110/unit with standard terms",
        estimated_cost_savings=1000.00,
    )
    
    # Create approval response (approved with no modifications)
    approval = ApprovalGateResponse(
        request_id="req-001",
        decision=ApprovalDecision.APPROVED,
        decision_maker="John Smith <john.smith@company.com>",
        justification="Approved - good negotiation strategy",
        modified_unit_price=None,
        modified_delivery_date=None,
        modified_payment_terms=None,
    )
    
    # Generate PO
    po = await agent.generate_purchase_order(
        recommendation=recommendation,
        approval=approval,
        requirements=requirements,
        vendor=vendor,
        workflow_id="workflow-123",
        buyer_name="Jane Doe",
        buyer_email="jane.doe@company.com",
    )
    
    # Verify PO fields
    assert po.po_number.startswith("PO-")
    assert po.vendor_id == "vendor-001"
    assert po.vendor_name == "AccuParts Inc"
    assert po.vendor_contact == "sales@accuparts.com"
    assert po.buyer_name == "Jane Doe"
    assert po.buyer_email == "jane.doe@company.com"
    assert po.product_id == "prod-001"
    assert po.product_name == "Industrial Sensor XYZ-100"
    assert po.quantity == 100
    assert po.unit == "pieces"
    assert po.unit_price == 110.00  # Negotiated price
    assert po.total_amount == 11000.00  # 100 * 110
    assert po.payment_terms == "Net 30"
    assert "CE" in po.required_certifications
    assert "UL" in po.required_certifications
    assert "ISO 9001" in po.required_certifications
    assert po.status == "draft"
    assert po.issued_at is None
    
    print(f"✓ PO generated: {po.po_number}")
    print(f"  Vendor: {po.vendor_name}")
    print(f"  Total: ${po.total_amount:,.2f}")
    print(f"  Unit price: ${po.unit_price:.2f} (negotiated)")


@pytest.mark.asyncio
async def test_generate_po_with_modified_terms():
    """Test PO generation with modified terms from approval."""
    agent = PurchaseOrderAgent()
    
    # Create product requirements
    requirements = ProductRequirements(
        product_id="prod-002",
        product_name="Power Supply Module",
        category="electronics",
        quantity=200,
        unit="pieces",
        required_certifications=["CE", "UL"],
        compliance_standards=["RoHS"],
        desired_delivery_date=datetime.now() + timedelta(days=14),
        max_lead_time_days=20,
    )
    
    # Create vendor profile
    vendor = VendorProfile(
        vendor_id="vendor-002",
        vendor_name="EuroComponent GmbH",
        country="Germany",
        certifications=["CE", "UL", "ISO 9001"],
        rating=4.5,
        contact_email="sales@eurocomponent.de",
        contact_phone="+49-555-0200",
        min_order_quantity=100,
        distance_miles=4200,
    )
    
    # Create negotiation recommendation
    recommendation = NegotiationRecommendation(
        recommendation_id="nego-002",
        vendor_id="vendor-002",
        vendor_name="EuroComponent GmbH",
        current_unit_price=95.00,
        suggested_unit_price=90.00,
        leverage_points=["Large order volume"],
        negotiation_strategy="Request volume discount",
        expected_outcome="Target: $90/unit",
        estimated_cost_savings=1000.00,
    )
    
    # Create approval response with MODIFICATIONS
    modified_delivery = datetime.now() + timedelta(days=21)
    approval = ApprovalGateResponse(
        request_id="req-002",
        decision=ApprovalDecision.APPROVED,
        decision_maker="Sarah Johnson <sarah.johnson@company.com>",
        justification="Approved with extended delivery and better payment terms",
        modified_unit_price=92.00,  # Slightly higher than negotiated
        modified_delivery_date=modified_delivery,  # Extended delivery
        modified_payment_terms="Net 45",  # Extended payment terms
    )
    
    # Generate PO
    po = await agent.generate_purchase_order(
        recommendation=recommendation,
        approval=approval,
        requirements=requirements,
        vendor=vendor,
        workflow_id="workflow-456",
    )
    
    # Verify modified fields are applied
    assert po.unit_price == 92.00  # Modified price (not 90.00)
    assert po.total_amount == 18400.00  # 200 * 92
    assert po.delivery_date == modified_delivery
    assert po.payment_terms == "Net 45"
    assert po.renegotiated_terms is not None
    assert "Unit price: $92.00" in po.renegotiated_terms
    assert "Payment: Net 45" in po.renegotiated_terms
    
    print(f"✓ PO generated with modified terms: {po.po_number}")
    print(f"  Modified price: ${po.unit_price:.2f} (was ${recommendation.suggested_unit_price:.2f})")
    print(f"  Modified payment: {po.payment_terms}")
    print(f"  Renegotiated terms: {po.renegotiated_terms}")


@pytest.mark.asyncio
async def test_issue_purchase_order():
    """Test issuing a draft PO."""
    agent = PurchaseOrderAgent()
    
    # Create minimal requirements and vendor for PO generation
    requirements = ProductRequirements(
        product_id="prod-003",
        product_name="Test Product",
        category="electronics",
        quantity=50,
    )
    
    vendor = VendorProfile(
        vendor_id="vendor-003",
        vendor_name="Test Vendor",
        country="USA",
        certifications=["CE"],
        rating=4.0,
        contact_email="test@vendor.com",
        contact_phone="+1-555-0300",
        min_order_quantity=10,
        distance_miles=1000,
    )
    
    recommendation = NegotiationRecommendation(
        recommendation_id="nego-003",
        vendor_id="vendor-003",
        vendor_name="Test Vendor",
        current_unit_price=100.00,
        suggested_unit_price=95.00,
        leverage_points=["Test"],
        negotiation_strategy="Test",
        expected_outcome="Test",
        estimated_cost_savings=250.00,
    )
    
    approval = ApprovalGateResponse(
        request_id="req-003",
        decision=ApprovalDecision.APPROVED,
        decision_maker="Test Approver <approver@company.com>",
    )
    
    # Generate draft PO
    po = await agent.generate_purchase_order(
        recommendation=recommendation,
        approval=approval,
        requirements=requirements,
        vendor=vendor,
        workflow_id="workflow-789",
    )
    
    assert po.status == "draft"
    assert po.issued_at is None
    
    # Issue the PO
    issued_po = await agent.issue_purchase_order(po)
    
    assert issued_po.status == "issued"
    assert issued_po.issued_at is not None
    assert isinstance(issued_po.issued_at, datetime)
    
    print(f"✓ PO issued: {issued_po.po_number}")
    print(f"  Status: {issued_po.status}")
    print(f"  Issued at: {issued_po.issued_at.strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    import asyncio
    
    print("Running Phase 7 Purchase Order Agent Tests...")
    print("=" * 60)
    
    asyncio.run(test_po_agent_initialization())
    asyncio.run(test_generate_purchase_order())
    asyncio.run(test_generate_po_with_modified_terms())
    asyncio.run(test_issue_purchase_order())
    
    print("=" * 60)
    print("All Phase 7 tests passed! ✓")
