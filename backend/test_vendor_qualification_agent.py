"""Quick test for VendorQualificationAgent"""
import asyncio
from datetime import datetime
from src.agents.workflows.rfq.models import ProductRequirements
from src.agents.workflows.rfq.agents.vendor_qualification_agent import VendorQualificationAgent


async def test_vendor_qualification():
    """Test vendor qualification agent"""
    # Create sample requirements
    requirements = ProductRequirements(
        product_id="PROD001",
        product_name="Precision Electronic Components",
        category="electronics",
        quantity=500,
        specifications={"voltage": "5V", "current": "2A"},
        required_certifications=["ISO 9001", "CE"],
        compliance_standards=["RoHS", "REACH"],
        desired_delivery_date=datetime(2024, 2, 15),
        max_lead_time_days=30,
        minimum_vendor_rating=4.0,
    )
    
    # Create agent and qualify vendors
    agent = VendorQualificationAgent()
    vendors = await agent.qualify(requirements, "WF001")
    
    print(f"✅ Qualified {len(vendors)} vendors:")
    for v in vendors[:3]:
        print(f"  - {v.vendor_name} (Rating: {v.overall_rating}, Lead time: {v.estimated_lead_time_days}d)")


if __name__ == "__main__":
    asyncio.run(test_vendor_qualification())
