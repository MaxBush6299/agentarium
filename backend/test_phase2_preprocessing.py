"""
Integration test for Phase 2 Preprocessing Stage
"""
import asyncio
from datetime import datetime
from src.agents.workflows.rfq.models import RFQRequest
from src.agents.workflows.rfq.orchestrators import PreprocessingOrchestrator


async def test_preprocessing_pipeline():
    """Test full preprocessing pipeline"""
    
    # Create RFQ request
    rfq_request = RFQRequest(
        request_id="REQ-001",
        requestor_name="John Smith",
        requestor_email="john@company.com",
        product_id="PROD001",
        product_name="Precision Electronic Components",
        category="electronics",
        quantity=500,
    )
    
    # Create orchestrator
    orchestrator = PreprocessingOrchestrator()
    
    # Execute preprocessing
    print("=" * 60)
    print("PREPROCESSING PIPELINE TEST")
    print("=" * 60)
    
    requirements, vendors = await orchestrator.preprocess(rfq_request, "WF-TEST-001")
    
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    
    print(f"\n✅ Product Requirements:")
    print(f"  Product: {requirements.product_name}")
    print(f"  Category: {requirements.category}")
    print(f"  Quantity: {requirements.quantity}")
    print(f"  Certifications: {requirements.required_certifications}")
    print(f"  Compliance: {requirements.compliance_standards}")
    print(f"  Lead time: {requirements.max_lead_time_days} days")
    print(f"  Min vendor rating: {requirements.minimum_vendor_rating} stars")
    
    print(f"\n✅ Qualified Vendors: {len(vendors)}")
    for i, vendor in enumerate(vendors, 1):
        print(f"  {i}. {vendor.vendor_name}")
        print(f"     Rating: {vendor.overall_rating}, Lead time: {vendor.estimated_lead_time_days}d")
        print(f"     Certifications: {', '.join(vendor.certifications)}")
        print(f"     Country: {vendor.country}")
    
    print("\n✅ Preprocessing pipeline test passed!")


if __name__ == "__main__":
    asyncio.run(test_preprocessing_pipeline())
