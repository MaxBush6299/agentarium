"""
Quote Parsing Agent for Phase 3

Collects and parses vendor quote responses.
Transforms vendor responses into standardized QuoteResponse objects.
"""

import logging
import asyncio
import random
from typing import List
from datetime import datetime, timedelta

from src.agents.workflows.rfq.models import (
    ProductRequirements,
    VendorProfile,
    RFQSubmission,
    QuoteResponse,
)
from src.agents.workflows.rfq.observability import rfq_logger

logger = logging.getLogger(__name__)


class QuoteParsingAgent:
    """
    Collects and parses vendor quote responses.
    
    Responsibilities:
    - Monitor/wait for quote responses from vendors
    - Parse vendor quote data into standardized QuoteResponse objects
    - Handle incomplete or missing responses with retry logic
    - Extract: unit price, bulk discounts, delivery date, payment terms, validity
    
    In production, this would:
    - Poll vendor APIs or email inboxes
    - Parse structured XML/JSON responses
    - Extract line items and pricing details
    - Validate response completeness
    
    For demo, simulates realistic vendor responses.
    """
    
    def __init__(self, agent_id: str = "quote_parsing_agent"):
        """Initialize quote parsing agent."""
        self.agent_id = agent_id
        self.logger = rfq_logger
    
    def _generate_simulated_quote(
        self,
        requirements: ProductRequirements,
        vendor: VendorProfile,
    ) -> QuoteResponse:
        """
        Generate simulated vendor quote based on vendor profile.
        
        Args:
            requirements: Product requirements
            vendor: Vendor profile
            
        Returns:
            Simulated QuoteResponse
        """
        # Base unit price varies by vendor rating and quality perception
        base_price = 100.0  # Base unit price
        
        # Higher-rated vendors charge more (quality premium)
        rating_factor = 1.0 + ((vendor.overall_rating - 3.0) * 0.15)
        
        # Add some randomness (+/- 10%)
        randomness = random.uniform(0.9, 1.1)
        
        unit_price = base_price * rating_factor * randomness
        
        # Quantity-based bulk discounts
        if requirements.quantity >= 1000:
            quantity_discount = 0.85
        elif requirements.quantity >= 500:
            quantity_discount = 0.90
        elif requirements.quantity >= 100:
            quantity_discount = 0.95
        else:
            quantity_discount = 1.0
        
        unit_price = unit_price * quantity_discount
        
        total_price = unit_price * requirements.quantity
        
        # Delivery date based on vendor lead time + buffer
        delivery_date = datetime.now() + timedelta(
            days=vendor.estimated_lead_time_days + random.randint(-2, 2)
        )
        
        # Create quote response
        quote = QuoteResponse(
            quote_id=f"QUOTE-{vendor.vendor_id}-{requirements.product_id}",
            submission_id=f"RFQ-{vendor.vendor_id}",
            vendor_id=vendor.vendor_id,
            vendor_name=vendor.vendor_name,
            unit_price=round(unit_price, 2),
            total_price=round(total_price, 2),
            currency="USD",
            delivery_date=delivery_date,
            delivery_lead_days=vendor.estimated_lead_time_days,
            payment_terms="Net 30",
            quote_validity_days=30,
            certifications_provided=vendor.certifications,
            compliance_guarantees=self._generate_special_terms(vendor),
        )
        
        return quote
    
    def _generate_special_terms(self, vendor: VendorProfile) -> str:
        """Generate vendor-specific special terms."""
        terms = []
        
        # Add terms based on vendor specialty
        if vendor.specialty:
            if "high-volume" in vendor.specialty.lower():
                terms.append("Volume commitment discounts available")
            if "automotive" in vendor.specialty.lower():
                terms.append("Automotive quality warranty included")
            if "medical" in vendor.specialty.lower():
                terms.append("FDA compliance certification included")
        
        # Add payment term variations
        if vendor.overall_rating >= 4.7:
            terms.append("Early payment discount: 2% if paid within 10 days")
        
        return "; ".join(terms) if terms else "Standard commercial terms"
    
    async def parse_quotes(
        self,
        requirements: ProductRequirements,
        vendors: List[VendorProfile],
        submissions: List[RFQSubmission],
        workflow_id: str,
    ) -> List[QuoteResponse]:
        """
        Collect and parse vendor quotes.
        
        Args:
            requirements: Product requirements
            vendors: List of vendors
            submissions: RFQ submissions sent to vendors
            workflow_id: Workflow ID for tracing
            
        Returns:
            List of parsed QuoteResponse objects
        """
        self.logger.info(
            f"Waiting for quote responses from {len(vendors)} vendors",
            workflow_id=workflow_id,
            stage="quote_parsing",
        )
        
        try:
            # Simulate waiting for vendor responses
            # In real system, would poll APIs or check email inbox
            await asyncio.sleep(0.2)
            
            # Generate quotes from all vendors (simulated)
            quotes = []
            for vendor in vendors:
                quote = self._generate_simulated_quote(requirements, vendor)
                quotes.append(quote)
                
                self.logger.info(
                    f"Parsed quote from {vendor.vendor_name}: ${quote.unit_price}/unit, "
                    f"Total: ${quote.total_price}, Delivery: {quote.delivery_date.strftime('%Y-%m-%d')}",
                    workflow_id=workflow_id,
                    stage="quote_parsing",
                    vendor_id=vendor.vendor_id,
                )
            
            self.logger.info(
                f"✅ Quote parsing complete: {len(quotes)} quotes collected",
                workflow_id=workflow_id,
                stage="quote_parsing",
            )
            
            return quotes
            
        except Exception as e:
            self.logger.error(
                f"Quote parsing failed: {e}",
                workflow_id=workflow_id,
                stage="quote_parsing",
            )
            raise


class QuoteParsingExecutor:
    """
    Executor for QuoteParsingAgent.
    Handles quote collection and parsing.
    """
    
    def __init__(self):
        """Initialize quote parsing executor."""
        self.agent = QuoteParsingAgent()
        self.logger = rfq_logger
    
    async def execute(
        self,
        requirements: ProductRequirements,
        vendors: List[VendorProfile],
        submissions: List[RFQSubmission],
        workflow_id: str,
    ) -> List[QuoteResponse]:
        """
        Execute quote parsing.
        
        Args:
            requirements: Product requirements
            vendors: List of vendors
            submissions: RFQ submissions
            workflow_id: Workflow ID for tracing
            
        Returns:
            List of QuoteResponse objects
        """
        return await self.agent.parse_quotes(
            requirements, vendors, submissions, workflow_id
        )
