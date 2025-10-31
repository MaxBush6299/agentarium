"""
Product Review Agent for RFQ Workflow

Analyzes product specifications and determines technical requirements for procurement.
This is the first stage in the sequential pre-processing pipeline.

Input: RFQRequest
Output: ProductRequirements
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from src.agents.workflows.rfq.models import (
    RFQRequest,
    ProductRequirements,
)
from src.agents.workflows.rfq.observability import (
    RFQEventType,
    RFQEvent,
    EventSeverity,
    rfq_logger,
)

logger = logging.getLogger(__name__)


class ProductReviewAgent:
    """
    Analyzes product information and determines procurement requirements.
    
    Responsibilities:
    1. Analyze product specifications from RFQ
    2. Determine category and market classification
    3. Identify required certifications and compliance standards
    4. Extract delivery constraints
    5. Determine vendor rating requirements
    
    Output: ProductRequirements model with complete specifications
    """
    
    def __init__(self, agent_id: str = "product_review_agent"):
        """
        Initialize ProductReviewAgent.
        
        Args:
            agent_id: Unique identifier for this agent
        """
        self.agent_id = agent_id
        self.logger = rfq_logger
    
    # ========================================================================
    # Certification and Compliance Mapping
    # ========================================================================
    
    # Certification requirements by category
    CATEGORY_CERTIFICATIONS = {
        "components": ["ISO 9001", "IPC"],
        "electronics": ["CE", "RoHS", "UL"],
        "industrial": ["ISO 9001", "ISO 14001"],
        "chemical": ["ISO 9001", "ISO 14001", "SDS"],
        "medical": ["FDA", "ISO 13485", "CE"],
        "automotive": ["ISO/TS 16949", "IATF"],
        "software": ["SOC 2", "ISO 27001"],
        "services": ["ISO 9001"],
    }
    
    # Compliance standards by category
    CATEGORY_COMPLIANCE = {
        "components": ["RoHS", "REACH"],
        "electronics": ["RoHS", "REACH", "WEEE"],
        "industrial": ["OSHA", "EPA"],
        "chemical": ["OSHA", "EPA", "TSCA"],
        "medical": ["FDA 21 CFR Part 11", "HIPAA"],
        "automotive": ["EPA", "DOT"],
        "software": ["GDPR", "CCPA"],
        "services": ["SOX"],
    }
    
    # Minimum vendor ratings by category
    CATEGORY_MIN_RATING = {
        "components": 3.5,
        "electronics": 4.0,
        "industrial": 3.5,
        "chemical": 4.0,
        "medical": 4.5,
        "automotive": 4.5,
        "software": 4.0,
        "services": 3.5,
    }
    
    # Default lead time by category (in days)
    CATEGORY_LEAD_TIME = {
        "components": 30,
        "electronics": 45,
        "industrial": 30,
        "chemical": 21,
        "medical": 60,
        "automotive": 45,
        "software": 7,
        "services": 14,
    }
    
    # ========================================================================
    # Main Processing Method
    # ========================================================================
    
    async def analyze(
        self,
        rfq_request: RFQRequest,
        workflow_id: str,
    ) -> ProductRequirements:
        """
        Analyze RFQ request and determine product requirements.
        
        Args:
            rfq_request: RFQRequest model with product information
            workflow_id: Workflow ID for tracing
            
        Returns:
            ProductRequirements with analyzed specifications
            
        Raises:
            ValueError: If required product information is missing
        """
        self.logger.info(
            f"Starting product review for {rfq_request.product_name}",
            workflow_id=workflow_id,
            stage="product_review"
        )
        
        try:
            # Validate input
            self._validate_rfq_request(rfq_request)
            
            # Extract and process specifications
            specifications = self._extract_specifications(rfq_request)
            
            # Determine certifications required
            required_certs = self._determine_certifications(rfq_request.category)
            
            # Determine compliance standards
            compliance_standards = self._determine_compliance(rfq_request.category)
            
            # Calculate delivery constraints
            desired_delivery = self._calculate_delivery_date(rfq_request)
            max_lead_time = self._determine_max_lead_time(rfq_request)
            
            # Determine vendor rating requirement
            min_rating = self._determine_vendor_rating(rfq_request.category)
            
            # Create ProductRequirements model
            requirements = ProductRequirements(
                product_id=rfq_request.product_id,
                product_name=rfq_request.product_name,
                category=rfq_request.category,
                quantity=rfq_request.quantity,
                unit=rfq_request.unit,
                specifications=specifications,
                required_certifications=required_certs,
                compliance_standards=compliance_standards,
                desired_delivery_date=desired_delivery,
                max_lead_time_days=max_lead_time,
                minimum_vendor_rating=min_rating,
                special_requirements=rfq_request.special_requirements,
            )
            
            self.logger.info(
                "Product review completed successfully",
                workflow_id=workflow_id,
                stage="product_review"
            )
            
            return requirements
            
        except Exception as e:
            self.logger.error(
                f"Product review failed: {e}",
                workflow_id=workflow_id,
                stage="product_review"
            )
            raise
    
    # ========================================================================
    # Validation Methods
    # ========================================================================
    
    def _validate_rfq_request(self, rfq_request: RFQRequest) -> None:
        """
        Validate that required RFQ fields are present.
        
        Args:
            rfq_request: RFQRequest to validate
            
        Raises:
            ValueError: If required fields are missing
        """
        required_fields = [
            "product_id",
            "product_name",
            "category",
            "quantity",
        ]
        
        for field in required_fields:
            if not getattr(rfq_request, field, None):
                raise ValueError(f"Required field missing: {field}")
    
    # ========================================================================
    # Specification Extraction
    # ========================================================================
    
    def _extract_specifications(self, rfq_request: RFQRequest) -> Dict[str, Any]:
        """
        Extract product specifications from RFQ.
        
        Args:
            rfq_request: RFQRequest with product info
            
        Returns:
            Dictionary of specifications
        """
        specifications = {
            "product_id": rfq_request.product_id,
            "product_name": rfq_request.product_name,
            "category": rfq_request.category,
            "quantity": rfq_request.quantity,
            "budget": rfq_request.budget_amount,
        }
        
        # Add any special requirements as specifications
        if rfq_request.special_requirements:
            specifications["special_requirements"] = rfq_request.special_requirements
        
        return specifications
    
    # ========================================================================
    # Certification Determination
    # ========================================================================
    
    def _determine_certifications(self, category: str) -> List[str]:
        """
        Determine required certifications based on product category.
        
        Args:
            category: Product category
            
        Returns:
            List of required certification codes
        """
        # Get base certifications for category
        certs = self.CATEGORY_CERTIFICATIONS.get(category.lower(), ["ISO 9001"])
        
        # Always include ISO 9001 for quality management
        if "ISO 9001" not in certs:
            certs.append("ISO 9001")
        
        return sorted(list(set(certs)))  # Remove duplicates and sort
    
    # ========================================================================
    # Compliance Determination
    # ========================================================================
    
    def _determine_compliance(self, category: str) -> List[str]:
        """
        Determine compliance standards based on product category.
        
        Args:
            category: Product category
            
        Returns:
            List of compliance standards
        """
        standards = self.CATEGORY_COMPLIANCE.get(category.lower(), [])
        return sorted(list(set(standards)))  # Remove duplicates and sort
    
    # ========================================================================
    # Delivery Constraint Calculation
    # ========================================================================
    
    def _calculate_delivery_date(self, rfq_request: RFQRequest) -> Optional[datetime]:
        """
        Calculate desired delivery date.
        
        Args:
            rfq_request: RFQRequest with timeline info
            
        Returns:
            Desired delivery datetime or None
        """
        if rfq_request.desired_delivery_date:
            return rfq_request.desired_delivery_date
        
        # Calculate default delivery date based on category
        lead_time = self.CATEGORY_LEAD_TIME.get(
            rfq_request.category.lower(),
            30  # Default 30 days
        )
        
        return datetime.utcnow() + timedelta(days=lead_time)
    
    def _determine_max_lead_time(self, rfq_request: RFQRequest) -> int:
        """
        Determine maximum acceptable lead time in days.
        
        Args:
            rfq_request: RFQRequest with timeline info
            
        Returns:
            Maximum lead time in days
        """
        if rfq_request.max_lead_time_days:
            return rfq_request.max_lead_time_days
        
        # Use category default
        return self.CATEGORY_LEAD_TIME.get(
            rfq_request.category.lower(),
            30  # Default 30 days
        )
    
    # ========================================================================
    # Vendor Rating Determination
    # ========================================================================
    
    def _determine_vendor_rating(self, category: str) -> float:
        """
        Determine minimum acceptable vendor rating based on category.
        
        Args:
            category: Product category
            
        Returns:
            Minimum vendor rating (0-5)
        """
        return self.CATEGORY_MIN_RATING.get(category.lower(), 3.5)


# ============================================================================
# Integration with Agent Framework
# ============================================================================

class ProductReviewAgentExecutor:
    """
    Wrapper for ProductReviewAgent to integrate with Microsoft Agent Framework.
    
    Handles async execution and event tracking.
    """
    
    def __init__(self, agent_id: str = "product_review_agent"):
        """Initialize executor."""
        self.agent = ProductReviewAgent(agent_id=agent_id)
        self.logger = rfq_logger
    
    async def execute(
        self,
        rfq_request: RFQRequest,
        workflow_id: str,
    ) -> ProductRequirements:
        """
        Execute product review.
        
        Args:
            rfq_request: RFQRequest to analyze
            workflow_id: Workflow ID for tracing
            
        Returns:
            ProductRequirements model
        """
        return await self.agent.analyze(rfq_request, workflow_id)
