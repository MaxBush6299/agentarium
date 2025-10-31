"""
Phase 7: Purchase Order Generation Agent

Generates formal purchase orders after human approval of negotiation recommendations.
"""

from datetime import datetime
from typing import Optional
import uuid

from src.agents.workflows.rfq.models import (
    PurchaseOrder,
    NegotiationRecommendation,
    ApprovalGateResponse,
    ProductRequirements,
    VendorProfile,
)
from src.agents.workflows.rfq.observability import rfq_logger


class PurchaseOrderAgent:
    """
    Generates purchase orders from approved negotiation recommendations.
    
    Responsibilities:
    - Generate unique PO numbers
    - Compile all order details (vendor, product, pricing, terms)
    - Include compliance requirements and certifications
    - Apply any renegotiated terms from human approval
    - Set appropriate delivery dates and payment terms
    - Create audit trail for PO issuance
    """
    
    def __init__(self, name: str = "Purchase Order Agent"):
        self.name = name
        rfq_logger.info(f"{self.name} initialized")
    
    async def generate_purchase_order(
        self,
        recommendation: NegotiationRecommendation,
        approval: ApprovalGateResponse,
        requirements: ProductRequirements,
        vendor: VendorProfile,
        workflow_id: str,
        buyer_name: str = "Procurement Manager",
        buyer_email: str = "procurement@company.com",
    ) -> PurchaseOrder:
        """
        Generate a purchase order from approved recommendation.
        
        Args:
            recommendation: Approved negotiation recommendation
            approval: Human approval response with any modifications
            requirements: Product requirements from Phase 2
            vendor: Selected vendor profile
            workflow_id: Workflow identifier for PO number generation
            buyer_name: Name of approving buyer
            buyer_email: Email of approving buyer
        
        Returns:
            PurchaseOrder object ready for issuance
        """
        rfq_logger.info(
            f"{self.name}: Generating PO for vendor {recommendation.vendor_name} "
            f"(workflow: {workflow_id})"
        )
        
        # Generate unique PO number
        po_number = self._generate_po_number(workflow_id)
        
        # Determine final pricing (use modified price if provided in approval)
        unit_price = (
            approval.modified_unit_price
            if approval.modified_unit_price is not None
            else recommendation.suggested_unit_price
        )
        
        total_amount = unit_price * requirements.quantity
        
        # Determine delivery date (use modified if provided)
        delivery_date = (
            approval.modified_delivery_date
            if approval.modified_delivery_date is not None
            else requirements.desired_delivery_date or datetime.now()
        )
        
        # Determine payment terms (use modified if provided)
        payment_terms = (
            approval.modified_payment_terms
            if approval.modified_payment_terms
            else "Net 30"
        )
        
        # Compile renegotiated terms for reference
        renegotiated_terms = None
        if approval.modified_unit_price or approval.modified_delivery_date or approval.modified_payment_terms:
            terms_list = []
            if approval.modified_unit_price:
                terms_list.append(f"Unit price: ${approval.modified_unit_price:.2f}")
            if approval.modified_delivery_date:
                terms_list.append(f"Delivery: {approval.modified_delivery_date.strftime('%Y-%m-%d')}")
            if approval.modified_payment_terms:
                terms_list.append(f"Payment: {approval.modified_payment_terms}")
            renegotiated_terms = "; ".join(terms_list)
        
        # Create PurchaseOrder
        purchase_order = PurchaseOrder(
            po_number=po_number,
            po_date=datetime.now(),
            vendor_id=recommendation.vendor_id,
            vendor_name=recommendation.vendor_name,
            vendor_contact=vendor.contact_email,
            buyer_name=buyer_name,
            buyer_email=buyer_email,
            product_id=requirements.product_id,
            product_name=requirements.product_name,
            quantity=requirements.quantity,
            unit=requirements.unit,
            unit_price=unit_price,
            total_amount=total_amount,
            delivery_date=delivery_date,
            payment_terms=payment_terms,
            required_certifications=requirements.required_certifications,
            compliance_requirements=", ".join(requirements.compliance_standards) if requirements.compliance_standards else None,
            renegotiated_terms=renegotiated_terms,
            quote_id=recommendation.recommendation_id,
            status="draft",
            issued_at=None,  # Will be set when PO is actually issued
            acknowledged_at=None,
        )
        
        rfq_logger.info(
            f"{self.name}: Generated PO {po_number} - "
            f"${total_amount:,.2f} for {requirements.quantity} {requirements.unit}"
        )
        
        return purchase_order
    
    def _generate_po_number(self, workflow_id: str) -> str:
        """
        Generate unique PO number.
        
        Format: PO-{workflow_id_prefix}-{timestamp}-{random}
        Example: PO-WF123-20251030-A3F9
        """
        timestamp = datetime.now().strftime("%Y%m%d")
        random_suffix = str(uuid.uuid4())[:4].upper()
        workflow_prefix = workflow_id[:6].upper() if workflow_id else "WFXXXX"
        
        return f"PO-{workflow_prefix}-{timestamp}-{random_suffix}"
    
    async def issue_purchase_order(self, purchase_order: PurchaseOrder) -> PurchaseOrder:
        """
        Issue the purchase order (mark as sent to vendor).
        
        In production, this would:
        - Send PO to vendor via email/API
        - Update ERP system
        - Trigger vendor notification
        
        For now, just updates status and timestamp.
        
        Args:
            purchase_order: Draft PO to issue
        
        Returns:
            Updated PO with issued status
        """
        rfq_logger.info(
            f"{self.name}: Issuing PO {purchase_order.po_number} to {purchase_order.vendor_name}"
        )
        
        purchase_order.status = "issued"
        purchase_order.issued_at = datetime.now()
        
        rfq_logger.info(
            f"{self.name}: PO {purchase_order.po_number} issued successfully"
        )
        
        return purchase_order
