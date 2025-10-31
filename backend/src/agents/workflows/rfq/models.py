"""
RFQ Workflow Data Models

Pydantic models for the parallel RFQ workflow including product requirements,
vendor information, quotes, evaluations, and purchase orders.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field


# ============================================================================
# Enumerations
# ============================================================================

class VendorStatus(str, Enum):
    """Vendor qualification status."""
    QUALIFIED = "qualified"
    PENDING_REVIEW = "pending_review"
    REJECTED = "rejected"
    BLACKLISTED = "blacklisted"


class RFQStatus(str, Enum):
    """RFQ submission status."""
    SUBMITTED = "submitted"
    ACKNOWLEDGED = "acknowledged"
    QUOTE_RECEIVED = "quote_received"
    NO_RESPONSE = "no_response"
    TIMED_OUT = "timed_out"
    CANCELLED = "cancelled"


class ApprovalDecision(str, Enum):
    """Human approval gate decisions."""
    APPROVED = "approved"
    REJECTED = "rejected"
    RENEGOTIATE = "renegotiate"
    MORE_INFO = "more_info"
    ABORT = "abort"


class RiskLevel(str, Enum):
    """Risk severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ============================================================================
# Core Data Models
# ============================================================================

class ProductRequirements(BaseModel):
    """
    Product specifications and requirements determined during review.
    
    Output from ProductReviewAgent.
    """
    product_id: str = Field(..., description="Unique product identifier")
    product_name: str = Field(..., description="Product name/description")
    category: str = Field(..., description="Product category for vendor matching")
    quantity: int = Field(..., ge=1, description="Quantity required")
    unit: str = Field(default="pieces", description="Unit of measurement")
    
    # Specifications
    specifications: Dict[str, Any] = Field(
        default_factory=dict,
        description="Technical specifications (materials, dimensions, tolerances, etc.)"
    )
    
    # Requirements
    required_certifications: List[str] = Field(
        default_factory=list,
        description="Required certifications (ISO, UL, CE, etc.)"
    )
    compliance_standards: List[str] = Field(
        default_factory=list,
        description="Compliance standards to meet (RoHS, REACH, etc.)"
    )
    
    # Delivery constraints
    desired_delivery_date: Optional[datetime] = Field(
        default=None,
        description="Desired delivery date"
    )
    max_lead_time_days: int = Field(
        default=30,
        description="Maximum acceptable lead time in days"
    )
    
    # Geographic constraints
    preferred_geography: Optional[List[str]] = Field(
        default=None,
        description="Preferred vendor locations/regions"
    )
    
    # Additional requirements
    minimum_vendor_rating: float = Field(
        default=3.5,
        ge=0.0,
        le=5.0,
        description="Minimum required vendor rating (0-5)"
    )
    special_requirements: Optional[str] = Field(
        default=None,
        description="Any special requirements or constraints"
    )
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class VendorProfile(BaseModel):
    """
    Vendor information for RFQ submission.
    
    Output from VendorQualificationAgent.
    """
    vendor_id: str = Field(..., description="Unique vendor identifier")
    vendor_name: str = Field(..., description="Vendor company name")
    contact_email: str = Field(..., description="Primary contact email")
    contact_phone: Optional[str] = Field(default=None, description="Contact phone")
    
    # Qualifications
    status: VendorStatus = Field(
        default=VendorStatus.QUALIFIED,
        description="Vendor qualification status"
    )
    certifications: List[str] = Field(
        default_factory=list,
        description="Vendor certifications held"
    )
    overall_rating: float = Field(
        default=0.0,
        ge=0.0,
        le=5.0,
        description="Historical vendor rating (0-5)"
    )
    
    # Capacity info
    estimated_lead_time_days: int = Field(
        default=14,
        description="Typical lead time for similar products (days)"
    )
    minimum_order_quantity: int = Field(
        default=1,
        description="Minimum order quantity"
    )
    
    # Location
    country: str = Field(..., description="Vendor country")
    region: Optional[str] = Field(default=None, description="Vendor region/state")
    
    # Additional info
    previous_orders: int = Field(
        default=0,
        description="Number of previous orders from this vendor"
    )
    specialty: Optional[str] = Field(
        default=None,
        description="Vendor specialty or focus area"
    )


class RFQSubmission(BaseModel):
    """
    RFQ submission record for tracking.
    
    Created when RFQ is sent to a vendor.
    """
    submission_id: str = Field(..., description="Unique submission identifier")
    vendor_id: str = Field(..., description="Target vendor ID")
    vendor_name: str = Field(..., description="Target vendor name")
    requirements: ProductRequirements = Field(..., description="Product requirements sent")
    
    status: RFQStatus = Field(
        default=RFQStatus.SUBMITTED,
        description="Current submission status"
    )
    
    submitted_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp of RFQ submission"
    )
    acknowledged_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp of vendor acknowledgment"
    )
    expected_response_date: Optional[datetime] = Field(
        default=None,
        description="Expected response deadline"
    )
    
    notes: Optional[str] = Field(
        default=None,
        description="Any notes about the submission"
    )


class QuoteResponse(BaseModel):
    """
    Vendor quote response to RFQ.
    
    Output from QuoteParsingAgent.
    """
    quote_id: str = Field(..., description="Unique quote identifier")
    submission_id: str = Field(..., description="Associated RFQ submission ID")
    vendor_id: str = Field(..., description="Responding vendor ID")
    vendor_name: str = Field(..., description="Responding vendor name")
    
    # Pricing
    unit_price: float = Field(..., ge=0, description="Unit price")
    currency: str = Field(default="USD", description="Currency code")
    total_price: float = Field(..., ge=0, description="Total price for quantity")
    
    # Bulk discounts (if applicable)
    bulk_discounts: Optional[Dict[int, float]] = Field(
        default=None,
        description="Bulk discount tiers: {quantity: discount_percentage}"
    )
    
    # Terms
    delivery_date: datetime = Field(..., description="Promised delivery date")
    delivery_lead_days: int = Field(..., ge=0, description="Lead time in days")
    payment_terms: str = Field(
        default="Net 30",
        description="Payment terms (e.g., 'Net 30', '2/10 Net 30')"
    )
    quote_validity_days: int = Field(
        default=30,
        description="How long quote is valid (days)"
    )
    
    # Quality/Compliance
    certifications_provided: List[str] = Field(
        default_factory=list,
        description="Certifications vendor provides"
    )
    compliance_guarantees: Optional[str] = Field(
        default=None,
        description="Compliance guarantees made by vendor"
    )
    
    # Response metadata
    received_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When quote was received"
    )
    response_source: str = Field(
        default="api",
        description="Source of quote (api, email, manual, simulated)"
    )
    
    notes: Optional[str] = Field(
        default=None,
        description="Additional notes from vendor"
    )


class VendorEvaluation(BaseModel):
    """
    Evaluation results for a vendor from parallel evaluation tracks.
    
    Produced by Review, Delivery, and Financial evaluation agents.
    """
    vendor_id: str = Field(..., description="Vendor being evaluated")
    vendor_name: str = Field(..., description="Vendor name")
    quote_id: Optional[str] = Field(default=None, description="Associated quote ID")
    
    # Review & Certification Track
    review_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=5.0,
        description="Vendor review/rating score"
    )
    certifications_verified: Optional[bool] = Field(
        default=None,
        description="All required certifications verified"
    )
    certification_details: Optional[Dict[str, bool]] = Field(
        default=None,
        description="Individual certification verification status"
    )
    compliance_status: Optional[str] = Field(
        default=None,
        description="Compliance status (compliant, non-compliant, pending)"
    )
    
    # Delivery & Logistics Track
    delivery_feasible: Optional[bool] = Field(
        default=None,
        description="Delivery date is feasible"
    )
    delivery_lead_assessment: Optional[str] = Field(
        default=None,
        description="Lead time assessment (on_time, tight, risky)"
    )
    geographic_risk: Optional[str] = Field(
        default=None,
        description="Geographic/shipping risk level (low, medium, high)"
    )
    delivery_confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence in meeting delivery commitment (0-1)"
    )
    
    # Financial Terms Track
    price_competitiveness: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Price competitiveness score (0=highest price, 1=best price)"
    )
    total_cost_of_ownership: Optional[float] = Field(
        default=None,
        description="Calculated total cost including all factors"
    )
    financial_risk_flags: Optional[List[str]] = Field(
        default=None,
        description="Financial risks identified (unusual terms, payment risk, etc.)"
    )
    
    # Overall assessment
    risk_level: Optional[RiskLevel] = Field(
        default=None,
        description="Overall risk assessment"
    )
    risk_factors: Optional[List[str]] = Field(
        default=None,
        description="Key risk factors identified"
    )
    
    evaluator_notes: Optional[str] = Field(
        default=None,
        description="Evaluator notes and recommendations"
    )
    
    evaluation_timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When evaluation was completed"
    )


class NormalizedQuote(BaseModel):
    """
    Normalized quote for comparison.
    
    Standardized representation of quote for side-by-side analysis.
    """
    quote_id: str = Field(..., description="Original quote ID")
    vendor_id: str = Field(..., description="Vendor ID")
    vendor_name: str = Field(..., description="Vendor name")
    
    # Normalized pricing
    unit_price: float = Field(..., ge=0, description="Unit price (normalized)")
    total_price: float = Field(..., ge=0, description="Total price")
    price_per_unit_with_bulk: float = Field(
        ...,
        ge=0,
        description="Effective unit price after bulk discounts"
    )
    
    # Normalized delivery
    delivery_date: datetime = Field(..., description="Promised delivery date")
    lead_time_days: int = Field(..., description="Lead time in days")
    
    # Scoring
    overall_score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Composite score (0-100)"
    )
    price_score: float = Field(0.0, ge=0.0, le=100.0, description="Price component score")
    delivery_score: float = Field(0.0, ge=0.0, le=100.0, description="Delivery component score")
    quality_score: float = Field(0.0, ge=0.0, le=100.0, description="Quality component score")
    
    # Flags
    risk_flags: List[str] = Field(
        default_factory=list,
        description="Risk flags for this vendor"
    )
    
    rank: Optional[int] = Field(
        default=None,
        description="Ranking position (1=best)"
    )


class ComparisonReport(BaseModel):
    """
    Comprehensive comparison report from all parallel evaluations.
    
    Output from ComparisonAndAnalysisAgent.
    """
    report_id: str = Field(..., description="Unique report ID")
    
    normalized_quotes: List[NormalizedQuote] = Field(
        ...,
        description="Normalized quotes for comparison"
    )
    vendor_evaluations: List[VendorEvaluation] = Field(
        ...,
        description="Complete evaluations from all tracks"
    )
    
    # Analysis
    top_ranked_vendors: List[Dict[str, Any]] = Field(
        ...,
        description="Top 3 vendors ranked with scores"
    )
    
    risk_summary: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Risk flags organized by vendor"
    )
    
    recommendations: str = Field(
        ...,
        description="Analysis recommendations"
    )
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class NegotiationRecommendation(BaseModel):
    """
    Negotiation strategy recommendations.
    
    Output from NegotiationStrategyAgent.
    """
    recommendation_id: str = Field(..., description="Unique recommendation ID")
    
    vendor_id: str = Field(..., description="Target vendor for negotiation")
    vendor_name: str = Field(..., description="Vendor name")
    
    # Leverage points
    leverage_points: List[str] = Field(
        default_factory=list,
        description="Identified leverage points for negotiation"
    )
    
    # Counter-offers
    suggested_unit_price: Optional[float] = Field(
        default=None,
        ge=0,
        description="Suggested counter-offer unit price"
    )
    suggested_payment_terms: Optional[str] = Field(
        default=None,
        description="Suggested payment term counter-offer"
    )
    suggested_delivery_date: Optional[datetime] = Field(
        default=None,
        description="Suggested delivery date counter-offer"
    )
    
    # Strategy
    negotiation_strategy: str = Field(
        ...,
        description="Recommended negotiation strategy"
    )
    expected_outcome: str = Field(
        ...,
        description="Expected outcome of negotiation"
    )
    fallback_options: Optional[List[str]] = Field(
        default=None,
        description="Fallback options if primary negotiation fails"
    )
    
    # Impact
    estimated_cost_savings: Optional[float] = Field(
        default=None,
        ge=0,
        description="Estimated cost savings from negotiation"
    )
    
    notes: Optional[str] = Field(default=None, description="Additional notes")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ApprovalRequest(BaseModel):
    """
    Human-in-the-loop approval request.
    
    Sent to decision-maker for approval/rejection.
    """
    request_id: str = Field(..., description="Unique request ID")
    
    comparison_report: ComparisonReport = Field(
        ...,
        description="Comparison analysis"
    )
    negotiation_recommendations: Optional[List[NegotiationRecommendation]] = Field(
        default=None,
        description="Negotiation recommendations"
    )
    
    recommended_vendor_id: Optional[str] = Field(
        default=None,
        description="Top recommended vendor ID"
    )
    recommended_vendor_name: Optional[str] = Field(
        default=None,
        description="Top recommended vendor name"
    )
    
    decision_required_by: datetime = Field(
        ...,
        description="Deadline for decision"
    )
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ApprovalGateResponse(BaseModel):
    """
    Response from human approval gate.
    
    Decision made by procurement manager/decision-maker.
    """
    request_id: str = Field(..., description="Associated approval request ID")
    decision: ApprovalDecision = Field(..., description="Decision made")
    
    # Approved vendor info (if decision is APPROVED)
    approved_vendor_id: Optional[str] = Field(
        default=None,
        description="Approved vendor ID"
    )
    approved_quote_id: Optional[str] = Field(
        default=None,
        description="Approved quote ID"
    )
    
    # Modifications (if decision is APPROVED or RENEGOTIATE)
    modified_unit_price: Optional[float] = Field(
        default=None,
        ge=0,
        description="Modified unit price if negotiated"
    )
    modified_delivery_date: Optional[datetime] = Field(
        default=None,
        description="Modified delivery date if negotiated"
    )
    modified_payment_terms: Optional[str] = Field(
        default=None,
        description="Modified payment terms if negotiated"
    )
    
    # Reasoning
    justification: Optional[str] = Field(
        default=None,
        description="Why this decision was made"
    )
    
    # Renegotiation feedback (if decision is RENEGOTIATE)
    renegotiation_feedback: Optional[str] = Field(
        default=None,
        description="Feedback for renegotiation strategy"
    )
    
    # Additional info request (if decision is MORE_INFO)
    info_requested: Optional[str] = Field(
        default=None,
        description="What additional information is needed"
    )
    
    decision_maker: str = Field(..., description="Decision maker name/email")
    decided_at: datetime = Field(default_factory=datetime.utcnow)


class PurchaseOrder(BaseModel):
    """
    Purchase Order document.
    
    Generated after approval.
    """
    po_number: str = Field(..., description="Unique PO number")
    po_date: datetime = Field(..., description="PO creation date")
    
    # Vendor
    vendor_id: str = Field(..., description="Vendor ID")
    vendor_name: str = Field(..., description="Vendor name")
    vendor_contact: str = Field(..., description="Vendor contact email")
    
    # Buyer
    buyer_name: str = Field(..., description="Buyer/approver name")
    buyer_email: str = Field(..., description="Buyer email")
    
    # Items
    product_id: str = Field(..., description="Product ID")
    product_name: str = Field(..., description="Product name")
    quantity: int = Field(..., ge=1, description="Quantity ordered")
    unit: str = Field(default="pieces", description="Unit of measurement")
    unit_price: float = Field(..., ge=0, description="Unit price")
    total_amount: float = Field(..., ge=0, description="Total order amount")
    
    # Terms
    delivery_date: datetime = Field(..., description="Expected delivery date")
    payment_terms: str = Field(default="Net 30", description="Payment terms")
    
    # Compliance
    required_certifications: List[str] = Field(
        default_factory=list,
        description="Required certifications"
    )
    compliance_requirements: Optional[str] = Field(
        default=None,
        description="Special compliance requirements"
    )
    
    # Reference
    renegotiated_terms: Optional[str] = Field(
        default=None,
        description="Any renegotiated terms from approval gate"
    )
    quote_id: Optional[str] = Field(
        default=None,
        description="Associated quote ID"
    )
    
    # Status
    status: str = Field(default="draft", description="PO status")
    issued_at: Optional[datetime] = Field(
        default=None,
        description="When PO was issued"
    )
    acknowledged_at: Optional[datetime] = Field(
        default=None,
        description="When vendor acknowledged PO"
    )


# ============================================================================
# RFQ Request (Input)
# ============================================================================

class RFQRequest(BaseModel):
    """
    Initial RFQ request to start the workflow.
    
    User input to begin the parallel RFQ process.
    """
    request_id: str = Field(..., description="Unique request ID")
    
    # Product info
    product_id: str = Field(..., description="Product to procure")
    product_name: str = Field(..., description="Product name/description")
    category: str = Field(..., description="Product category")
    quantity: int = Field(..., ge=1, description="Quantity needed")
    unit: str = Field(default="pieces", description="Unit of measurement")
    
    # Requirements
    required_certifications: Optional[List[str]] = Field(
        default=None,
        description="Required certifications"
    )
    special_requirements: Optional[str] = Field(
        default=None,
        description="Special requirements or constraints"
    )
    
    # Timeline
    desired_delivery_date: Optional[datetime] = Field(
        default=None,
        description="Desired delivery date"
    )
    max_lead_time_days: Optional[int] = Field(
        default=30,
        description="Maximum acceptable lead time"
    )
    
    # Budget
    budget_amount: Optional[float] = Field(
        default=None,
        ge=0,
        description="Budget available for this purchase"
    )
    
    # Decision maker
    requestor_name: str = Field(..., description="Who is requesting this RFQ")
    requestor_email: str = Field(..., description="Requestor email")
    approver_name: Optional[str] = Field(default=None, description="Who will approve")
    approver_email: Optional[str] = Field(default=None, description="Approver email")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
