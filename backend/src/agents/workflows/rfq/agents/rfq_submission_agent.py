"""
RFQ Submission Agent for Phase 3

Handles parallel submission of RFQs to multiple vendors concurrently.
Each vendor receives an RFQ with the product requirements and can be submitted in parallel.

Pattern: Creates RFQSubmission objects for each vendor
"""

import logging
import asyncio
from typing import List
from datetime import datetime
import uuid

from src.agents.workflows.rfq.models import (
    ProductRequirements,
    VendorProfile,
    RFQSubmission,
    RFQStatus,
)
from src.agents.workflows.rfq.observability import rfq_logger

logger = logging.getLogger(__name__)


class RFQSubmissionAgent:
    """
    Submits RFQ to a single vendor.
    
    This agent is designed to run in parallel for each vendor.
    It prepares and submits an RFQ request, simulating vendor contact.
    
    In a real system, this would:
    - Send email via Email API
    - Call vendor portal API
    - Use MCP tool for vendor contact
    - Await confirmation
    
    For now, it simulates vendor submission with realistic timing.
    """
    
    def __init__(self, agent_id: str = "rfq_submission_agent"):
        """Initialize RFQ submission agent."""
        self.agent_id = agent_id
        self.logger = rfq_logger
    
    async def submit_rfq(
        self,
        requirements: ProductRequirements,
        vendor: VendorProfile,
        workflow_id: str,
    ) -> RFQSubmission:
        """
        Submit RFQ to a single vendor.
        
        Args:
            requirements: ProductRequirements to submit
            vendor: Target vendor
            workflow_id: Workflow ID for tracing
            
        Returns:
            RFQSubmission object with submission details
        """
        submission_id = f"RFQ-{workflow_id}-{vendor.vendor_id}-{uuid.uuid4().hex[:6]}"
        
        self.logger.info(
            f"Submitting RFQ to {vendor.vendor_name}",
            workflow_id=workflow_id,
            stage="rfq_submission",
            vendor_id=vendor.vendor_id,
        )
        
        try:
            # Simulate vendor contact delay (network latency)
            await asyncio.sleep(0.05)
            
            # Create RFQ submission record
            submission = RFQSubmission(
                submission_id=submission_id,
                vendor_id=vendor.vendor_id,
                vendor_name=vendor.vendor_name,
                requirements=requirements,
                status=RFQStatus.SUBMITTED,
                notes=f"RFQ submitted to {vendor.vendor_name} at {vendor.contact_email}",
            )
            
            self.logger.info(
                f"✅ RFQ submitted to {vendor.vendor_name}",
                workflow_id=workflow_id,
                stage="rfq_submission",
                vendor_id=vendor.vendor_id,
                submission_id=submission_id,
            )
            
            return submission
            
        except Exception as e:
            self.logger.error(
                f"Failed to submit RFQ to {vendor.vendor_name}: {e}",
                workflow_id=workflow_id,
                stage="rfq_submission",
                vendor_id=vendor.vendor_id,
            )
            raise


class RFQSubmissionExecutor:
    """
    Executor for RFQSubmissionAgent - handles parallel execution.
    
    This executor manages concurrent RFQ submissions to multiple vendors.
    All submissions happen in parallel for efficiency.
    """
    
    def __init__(self):
        """Initialize submission executor."""
        self.agent = RFQSubmissionAgent()
        self.logger = rfq_logger
    
    async def submit_to_all_vendors(
        self,
        requirements: ProductRequirements,
        vendors: List[VendorProfile],
        workflow_id: str,
    ) -> List[RFQSubmission]:
        """
        Submit RFQ to all vendors in parallel.
        
        Args:
            requirements: ProductRequirements
            vendors: List of qualified vendors
            workflow_id: Workflow ID for tracing
            
        Returns:
            List of RFQSubmission objects (one per vendor)
        """
        self.logger.info(
            f"Starting parallel RFQ submission to {len(vendors)} vendors",
            workflow_id=workflow_id,
            stage="rfq_submission",
        )
        
        # Submit to all vendors concurrently
        submission_tasks = [
            self.agent.submit_rfq(requirements, vendor, workflow_id)
            for vendor in vendors
        ]
        
        try:
            submissions = await asyncio.gather(*submission_tasks)
            
            self.logger.info(
                f"✅ Parallel RFQ submission complete: {len(submissions)}/{len(vendors)} successful",
                workflow_id=workflow_id,
                stage="rfq_submission",
            )
            
            return submissions
            
        except Exception as e:
            self.logger.error(
                f"Parallel RFQ submission failed: {e}",
                workflow_id=workflow_id,
                stage="rfq_submission",
            )
            raise
