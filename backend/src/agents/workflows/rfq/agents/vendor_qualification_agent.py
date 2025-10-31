"""
Vendor Qualification Agent for RFQ Workflow

Queries the database for qualified vendors and filters them based on requirements.
This is the second stage in the sequential pre-processing pipeline.

Input: ProductRequirements
Output: List[VendorProfile]
"""

import logging
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.agents.workflows.rfq.models import (
    ProductRequirements,
    VendorProfile,
    VendorStatus,
)
from src.agents.workflows.rfq.observability import (
    RFQEventType,
    RFQEvent,
    EventSeverity,
    rfq_logger,
)

logger = logging.getLogger(__name__)


class VendorQualificationAgent:
    """
    Queries and filters vendors for RFQ process.
    
    Responsibilities:
    1. Query vendor database by product category
    2. Filter by required certifications
    3. Filter by minimum vendor rating
    4. Filter by geographic availability
    5. Check vendor capacity for requested quantity
    6. Assess lead time availability
    7. Return qualified vendor list
    
    Output: List of VendorProfile objects sorted by rating
    """
    
    def __init__(
        self,
        agent_id: str = "vendor_qualification_agent",
        use_sql_agent: bool = True,
    ):
        """
        Initialize VendorQualificationAgent.
        
        Args:
            agent_id: Unique identifier for this agent
            use_sql_agent: Whether to use SQL agent for database queries
        """
        self.agent_id = agent_id
        self.logger = rfq_logger
        self.use_sql_agent = use_sql_agent
        
        # Simulation mode for demo/testing
        self.simulation_mode = True
        self._simulated_vendors = self._create_simulated_vendors()
    
    # ========================================================================
    # Simulated Vendor Database (for demo/testing)
    # ========================================================================
    
    def _create_simulated_vendors(self) -> List[Dict[str, Any]]:
        """Create simulated vendor database for demo purposes."""
        return [
            {
                "vendor_id": "V001",
                "vendor_name": "AccuParts Industries",
                "contact_email": "orders@accuparts.com",
                "contact_phone": "+1-555-001-0001",
                "certifications": ["ISO 9001", "IPC", "ISO 14001"],
                "overall_rating": 4.7,
                "estimated_lead_time_days": 14,
                "minimum_order_quantity": 10,
                "country": "USA",
                "region": "California",
                "previous_orders": 45,
                "specialty": "Precision components",
                "capacity_units_per_month": 50000,
                "distance_miles": 2000,  # West Coast USA
            },
            {
                "vendor_id": "V002",
                "vendor_name": "Global Manufacturing Co.",
                "contact_email": "sales@globalmfg.com",
                "contact_phone": "+1-555-002-0002",
                "certifications": ["ISO 9001", "CE"],
                "overall_rating": 3.9,
                "estimated_lead_time_days": 25,
                "minimum_order_quantity": 100,
                "country": "Mexico",
                "region": "Monterrey",
                "previous_orders": 28,
                "specialty": "High-volume production",
                "capacity_units_per_month": 500000,
                "distance_miles": 1800,  # Mexico
            },
            {
                "vendor_id": "V003",
                "vendor_name": "EuroComponent GmbH",
                "contact_email": "info@eurocomponent.de",
                "contact_phone": "+49-30-555-0003",
                "certifications": ["ISO 9001", "ISO 14001", "IATF", "IPC"],
                "overall_rating": 4.5,
                "estimated_lead_time_days": 32,
                "minimum_order_quantity": 50,
                "country": "Germany",
                "region": "Berlin",
                "previous_orders": 32,
                "specialty": "Automotive components",
                "capacity_units_per_month": 100000,
                "distance_miles": 4200,  # Europe
            },
            {
                "vendor_id": "V004",
                "vendor_name": "TechSupply Asia Ltd.",
                "contact_email": "procurement@techsupply-asia.com",
                "contact_phone": "+86-10-555-0004",
                "certifications": ["ISO 9001"],
                "overall_rating": 3.5,
                "estimated_lead_time_days": 42,
                "minimum_order_quantity": 500,
                "country": "China",
                "region": "Shanghai",
                "previous_orders": 12,
                "specialty": "Electronics assembly",
                "capacity_units_per_month": 1000000,
                "distance_miles": 5600,  # Asia - longest distance
            },
            {
                "vendor_id": "V005",
                "vendor_name": "Quality Components LLC",
                "contact_email": "contact@qualitycomponents.com",
                "contact_phone": "+1-555-005-0005",
                "certifications": ["ISO 9001", "ISO 13485", "FDA", "ISO 14001", "IPC"],
                "overall_rating": 4.8,
                "estimated_lead_time_days": 10,
                "minimum_order_quantity": 1,
                "country": "USA",
                "region": "Massachusetts",
                "previous_orders": 67,
                "specialty": "Medical device components",
                "capacity_units_per_month": 50000,
                "distance_miles": 200,  # East Coast USA - closest
            },
        ]
    
    # ========================================================================
    # Main Processing Method
    # ========================================================================
    
    async def qualify(
        self,
        requirements: ProductRequirements,
        workflow_id: str,
    ) -> List[VendorProfile]:
        """
        Qualify vendors based on product requirements.
        
        Args:
            requirements: ProductRequirements from product review agent
            workflow_id: Workflow ID for tracing
            
        Returns:
            List of qualified VendorProfile objects, sorted by rating
            
        Raises:
            ValueError: If no vendors are qualified
        """
        self.logger.info(
            f"Starting vendor qualification for {requirements.product_name}",
            workflow_id=workflow_id,
            stage="vendor_qualification"
        )
        
        try:
            # Query vendors from database
            vendors = await self._query_vendors(
                category=requirements.category,
                workflow_id=workflow_id,
            )
            
            if not vendors:
                raise ValueError(f"No vendors found for category: {requirements.category}")
            
            # Filter vendors based on requirements
            qualified_vendors = self._filter_vendors(
                vendors=vendors,
                requirements=requirements,
            )
            
            if not qualified_vendors:
                self.logger.warning(
                    f"No vendors qualified for requirements",
                    workflow_id=workflow_id,
                    stage="vendor_qualification"
                )
                # Return top vendors even if not fully qualified
                qualified_vendors = sorted(
                    vendors,
                    key=lambda v: v.overall_rating,
                    reverse=True
                )[:3]
            
            # Sort by rating (descending)
            qualified_vendors = sorted(
                qualified_vendors,
                key=lambda v: v.overall_rating,
                reverse=True
            )
            
            self.logger.info(
                f"Vendor qualification completed: {len(qualified_vendors)} vendors qualified",
                workflow_id=workflow_id,
                stage="vendor_qualification"
            )
            
            return qualified_vendors
            
        except Exception as e:
            self.logger.error(
                f"Vendor qualification failed: {e}",
                workflow_id=workflow_id,
                stage="vendor_qualification"
            )
            raise
    
    # ========================================================================
    # Vendor Query Methods
    # ========================================================================
    
    async def _query_vendors(
        self,
        category: str,
        workflow_id: str,
    ) -> List[VendorProfile]:
        """
        Query vendors by product category.
        
        Args:
            category: Product category
            workflow_id: Workflow ID for tracing
            
        Returns:
            List of vendors in category
        """
        self.logger.info(
            f"Querying vendors for category: {category}",
            workflow_id=workflow_id,
            stage="vendor_qualification"
        )
        
        if self.simulation_mode:
            # Simulate database query delay
            await asyncio.sleep(0.1)
            vendor_data = self._simulated_vendors
        else:
            # In production, call SQL agent to query database
            # TODO: Integrate with SQL agent tool
            vendor_data = []
        
        # Convert raw vendor data to VendorProfile models
        vendors = []
        for vendor_dict in vendor_data:
            try:
                vendor = VendorProfile(
                    vendor_id=str(vendor_dict.get("vendor_id", "")),
                    vendor_name=str(vendor_dict.get("vendor_name", "")),
                    contact_email=str(vendor_dict.get("contact_email", "")),
                    contact_phone=vendor_dict.get("contact_phone"),
                    certifications=vendor_dict.get("certifications", []),
                    overall_rating=vendor_dict.get("overall_rating", 0.0),
                    estimated_lead_time_days=vendor_dict.get("estimated_lead_time_days", 30),
                    minimum_order_quantity=vendor_dict.get("minimum_order_quantity", 1),
                    country=str(vendor_dict.get("country", "")),
                    region=vendor_dict.get("region"),
                    previous_orders=vendor_dict.get("previous_orders", 0),
                    specialty=vendor_dict.get("specialty"),
                    status=VendorStatus.PENDING_REVIEW,
                )
                vendors.append(vendor)
            except Exception as e:
                self.logger.warning(
                    f"Error creating vendor profile for {vendor_dict.get('vendor_id')}: {e}",
                    workflow_id=workflow_id,
                )
                continue
        
        return vendors
    
    # ========================================================================
    # Vendor Filtering Methods
    # ========================================================================
    
    def _filter_vendors(
        self,
        vendors: List[VendorProfile],
        requirements: ProductRequirements,
    ) -> List[VendorProfile]:
        """
        Filter vendors based on requirements.
        
        Args:
            vendors: List of available vendors
            requirements: Product requirements to match
            
        Returns:
            List of vendors meeting all requirements
        """
        qualified = vendors
        
        # Filter by minimum vendor rating
        qualified = [
            v for v in qualified
            if v.overall_rating >= requirements.minimum_vendor_rating
        ]
        
        # Filter by required certifications
        qualified = [
            v for v in qualified
            if self._has_required_certifications(
                v.certifications,
                requirements.required_certifications
            )
        ]
        
        # Filter by minimum order quantity capability
        qualified = [
            v for v in qualified
            if v.minimum_order_quantity <= requirements.quantity
        ]
        
        # Filter by geographic preference (if specified)
        if requirements.preferred_geography:
            qualified = [
                v for v in qualified
                if v.country in requirements.preferred_geography
                or v.region in requirements.preferred_geography
            ]
        
        return qualified
    
    def _has_required_certifications(
        self,
        vendor_certs: List[str],
        required_certs: List[str],
    ) -> bool:
        """
        Check if vendor has all required certifications.
        
        Args:
            vendor_certs: Certifications vendor has
            required_certs: Certifications required
            
        Returns:
            True if vendor has all required certs
        """
        if not required_certs:
            return True
        
        vendor_certs_set = set(vendor_certs)
        required_certs_set = set(required_certs)
        
        return required_certs_set.issubset(vendor_certs_set)


# ============================================================================
# Integration with Agent Framework
# ============================================================================

class VendorQualificationAgentExecutor:
    """
    Wrapper for VendorQualificationAgent to integrate with Microsoft Agent Framework.
    
    Handles async execution and event tracking.
    """
    
    def __init__(
        self,
        agent_id: str = "vendor_qualification_agent",
        use_sql_agent: bool = True,
    ):
        """Initialize executor."""
        self.agent = VendorQualificationAgent(
            agent_id=agent_id,
            use_sql_agent=use_sql_agent,
        )
        self.logger = rfq_logger
    
    async def execute(
        self,
        requirements: ProductRequirements,
        workflow_id: str,
    ) -> List[VendorProfile]:
        """
        Execute vendor qualification.
        
        Args:
            requirements: ProductRequirements from product review
            workflow_id: Workflow ID for tracing
            
        Returns:
            List of qualified VendorProfile objects
        """
        return await self.agent.qualify(requirements, workflow_id)
