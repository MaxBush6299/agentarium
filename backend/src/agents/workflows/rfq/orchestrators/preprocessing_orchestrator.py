"""
Preprocessing Orchestrator for RFQ Workflow

Orchestrates the sequential preprocessing stage:
1. ProductReviewAgent analyzes product requirements
2. VendorQualificationAgent queries and filters vendors

Input: RFQRequest
Output: (ProductRequirements, List[VendorProfile])
"""

import logging
import asyncio
from typing import Tuple, List
from datetime import datetime

from src.agents.workflows.rfq.models import (
    RFQRequest,
    ProductRequirements,
    VendorProfile,
)
from src.agents.workflows.rfq.agents.product_review_agent import ProductReviewAgent
from src.agents.workflows.rfq.agents.vendor_qualification_agent import VendorQualificationAgent
from src.agents.workflows.rfq.observability import rfq_logger

logger = logging.getLogger(__name__)


class PreprocessingOrchestrator:
    """
    Orchestrates the sequential preprocessing stage.
    
    This is the first stage in the RFQ workflow that runs sequentially:
    1. Receives RFQRequest from user/system
    2. ProductReviewAgent analyzes product and determines requirements
    3. VendorQualificationAgent queries DB and finds qualified vendors
    4. Returns both intermediate outputs for next stage (parallel evaluation)
    
    Responsibilities:
    - Coordinate agent execution
    - Handle state transitions
    - Persist intermediate results
    - Provide observability and logging
    - Handle errors and fallbacks
    """
    
    def __init__(self):
        """Initialize preprocessing orchestrator."""
        self.logger = rfq_logger
        self.product_review_agent = ProductReviewAgent()
        self.vendor_qualification_agent = VendorQualificationAgent()
    
    # ========================================================================
    # Main Orchestration Method
    # ========================================================================
    
    async def preprocess(
        self,
        rfq_request: RFQRequest,
        workflow_id: str,
    ) -> Tuple[ProductRequirements, List[VendorProfile]]:
        """
        Execute preprocessing stage.
        
        Sequential flow:
        1. Validate RFQ request
        2. ProductReviewAgent → extract requirements
        3. VendorQualificationAgent → find qualified vendors
        4. Return intermediate state for next stage
        
        Args:
            rfq_request: Initial RFQ request
            workflow_id: Workflow ID for tracing
            
        Returns:
            Tuple of (ProductRequirements, List[VendorProfile])
            
        Raises:
            ValueError: If validation fails
        """
        self.logger.info(
            f"Starting preprocessing for RFQ: {rfq_request.product_name}",
            workflow_id=workflow_id,
            stage="preprocessing"
        )
        
        start_time = datetime.now()
        
        try:
            # ================================================================
            # Stage 1: Product Review Agent
            # ================================================================
            self.logger.info(
                "Stage 1: Product Review Agent",
                workflow_id=workflow_id,
                stage="preprocessing"
            )
            
            requirements = await self.product_review_agent.analyze(
                rfq_request=rfq_request,
                workflow_id=workflow_id,
            )
            
            self.logger.info(
                f"✅ Product Review complete: Category={requirements.category}, "
                f"Qty={requirements.quantity}, Certs={len(requirements.required_certifications)}",
                workflow_id=workflow_id,
                stage="preprocessing"
            )
            
            # ================================================================
            # Stage 2: Vendor Qualification Agent
            # ================================================================
            self.logger.info(
                "Stage 2: Vendor Qualification Agent",
                workflow_id=workflow_id,
                stage="preprocessing"
            )
            
            qualified_vendors = await self.vendor_qualification_agent.qualify(
                requirements=requirements,
                workflow_id=workflow_id,
            )
            
            self.logger.info(
                f"✅ Vendor Qualification complete: {len(qualified_vendors)} vendors qualified",
                workflow_id=workflow_id,
                stage="preprocessing"
            )
            
            # ================================================================
            # Return State
            # ================================================================
            end_time = datetime.now()
            duration_seconds = (end_time - start_time).total_seconds()
            
            self.logger.info(
                f"✅ Preprocessing complete in {duration_seconds:.2f}s",
                workflow_id=workflow_id,
                stage="preprocessing"
            )
            
            return (requirements, qualified_vendors)
            
        except Exception as e:
            self.logger.error(
                f"Preprocessing failed: {e}",
                workflow_id=workflow_id,
                stage="preprocessing"
            )
            raise


# ============================================================================
# Integration with Agent Framework
# ============================================================================

class PreprocessingOrchestratorExecutor:
    """
    Wrapper for PreprocessingOrchestrator to integrate with Agent Framework.
    
    Handles async execution and framework integration.
    """
    
    def __init__(self):
        """Initialize executor."""
        self.orchestrator = PreprocessingOrchestrator()
        self.logger = rfq_logger
    
    async def execute(
        self,
        rfq_request: RFQRequest,
        workflow_id: str,
    ) -> Tuple[ProductRequirements, List[VendorProfile]]:
        """
        Execute preprocessing orchestration.
        
        Args:
            rfq_request: Initial RFQ request
            workflow_id: Workflow ID for tracing
            
        Returns:
            Tuple of (ProductRequirements, List[VendorProfile])
        """
        return await self.orchestrator.preprocess(rfq_request, workflow_id)
