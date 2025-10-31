"""
LLM Integration for RFQ Workflow - Phase 3+ Design

This module provides LLM-enhanced agents for the parallel evaluation stage.
Following the factory + base agent pattern from existing codebase.

Pattern Recognition from factory.py + base.py:
1. AgentFactory.create_from_metadata() creates DemoBaseAgent instances
2. DemoBaseAgent wraps ChatAgent from agent_framework
3. Agents receive tools (MCP, OpenAPI) and instructions (system_prompt)
4. ChatAgent handles all LLM orchestration via Azure OpenAI

For RFQ Phase 3, we'll follow this same pattern:
1. LLMEvaluationAgent(DemoBaseAgent) - adds LLM reasoning to evaluation logic
2. Provide system prompts for nuanced analysis
3. Use factory pattern to instantiate from config
4. Keep rule-based logic for deterministic parts
"""

import logging
import json
import re
import unicodedata
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

from src.agents.base import DemoBaseAgent
from src.agents.workflows.rfq.models import (
    ProductRequirements,
    VendorProfile,
    QuoteResponse,
    VendorEvaluation,
    RiskLevel,
)
from src.agents.workflows.rfq.observability import rfq_logger

logger = logging.getLogger(__name__)


def decode_unicode_safely(text: str) -> str:
    """Remove problematic unicode characters that cause encoding issues on Windows terminals."""
    if not isinstance(text, str):
        return str(text)
    # Use NFKD normalization and ignore errors, removing most unicode characters
    try:
        return text.encode('utf-8', errors='ignore').decode('utf-8')
    except Exception:
        # Fallback: just get ASCII representation
        return ''.join(c if ord(c) < 128 else '?' for c in text)


# ============================================================================
# LLM-Enhanced Evaluation Agents for Phase 3 (Parallel Tracks)
# ============================================================================

class CertificationComplianceEvaluator(DemoBaseAgent):
    """
    Track 1: Nuanced certification & compliance analysis using LLM.
    
    Unlike ProductReviewAgent (rule-based), this analyzes the QUALITY of compliance:
    - Does vendor have certifications? (rule-based: YES/NO)
    - Are certifications current and legitimate? (LLM-enhanced)
    - Any red flags in compliance history? (LLM analysis)
    - Recommendation: APPROVE / FLAG CONCERN / REJECT
    
    System Prompt Strategy:
    - Provide certification requirements as context
    - Give vendor profiles and documentation
    - Ask LLM to assess compliance QUALITY
    - Return structured decision with reasoning
    """
    
    SYSTEM_PROMPT = """
You are a specialized compliance analyst for RFQ evaluation.

Your role: Analyze vendor certifications and compliance documentation for QUALITY.

You are given:
1. Product requirements (needed certifications/standards)
2. Vendor profile (claimed certifications)
3. Vendor history (past compliance issues)

Your task:
- Verify claimed certifications are legitimate (not outdated, not fraudulent)
- Identify potential red flags or compliance gaps
- Assess risk level of vendor
- Provide recommendation: APPROVE / FLAG CONCERN / REJECT

Output format:
```json
{
    "vendor_id": "V001",
    "compliance_assessment": "description of findings",
    "red_flags": ["flag1", "flag2"],
    "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
    "recommendation": "APPROVE|FLAG_CONCERN|REJECT",
    "confidence": 0.95,
    "reasoning": "detailed explanation"
}
```
"""
    
    def __init__(self, requirements: ProductRequirements):
        """
        Initialize compliance evaluator.
        
        Args:
            requirements: ProductRequirements specifying needed certifications
        """
        self.requirements = requirements
        
        # Customize prompt with actual requirements
        custom_prompt = self.SYSTEM_PROMPT + f"""

REQUIRED CERTIFICATIONS FOR THIS RFQ:
{', '.join(requirements.required_certifications)}

REQUIRED COMPLIANCE STANDARDS:
{', '.join(requirements.compliance_standards)}

CATEGORY: {requirements.category}
QUANTITY: {requirements.quantity}
"""
        
        super().__init__(
            name="Certification Compliance Evaluator",
            instructions=custom_prompt,
            model="gpt-4o",
            temperature=0.3,  # Lower temp for analytical consistency
        )
        
        logger.info(f"CertificationComplianceEvaluator initialized for {requirements.category}")
    
    async def evaluate_vendor_compliance(
        self,
        vendor: VendorProfile,
        workflow_id: str,
    ) -> Dict[str, Any]:
        """
        Evaluate vendor compliance using LLM.
        
        Args:
            vendor: Vendor to evaluate
            workflow_id: Workflow ID for tracing
            
        Returns:
            LLM evaluation result with risk_level, recommendation, reasoning
        """
        # Calculate compliance score based on certifications and track record
        num_certs = len(vendor.certifications)
        cert_score = min(100, num_certs * 15)  # Each cert worth 15 points, max 100
        
        # Rating factor: 4.5+ is excellent, 3.5-4.5 is good, <3.5 is risky
        if vendor.overall_rating >= 4.5:
            rating_factor = "STRONG"
        elif vendor.overall_rating >= 3.8:
            rating_factor = "MODERATE"
        else:
            rating_factor = "WEAK"
        
        # Track record
        track_record = "established" if vendor.previous_orders > 25 else "developing"
        
        prompt = f"""
EVALUATE THIS VENDOR:

Vendor: {vendor.vendor_name}
Certifications: {', '.join(vendor.certifications)} ({num_certs} total)
Overall Rating: {vendor.overall_rating}/5.0 ({rating_factor})
Track Record: {vendor.previous_orders} previous orders ({track_record})
Country: {vendor.country}
Specialty: {vendor.specialty}

Assess compliance based on:
1. Certification strength ({num_certs} certifications)
2. Vendor rating history ({vendor.overall_rating}/5.0 with {vendor.previous_orders} orders)
3. Specialty alignment (do they specialize in this area?)

Certifications provide baseline compliance score of {cert_score}/100.
Confidence should be {cert_score/100:.2f} based on certifications alone.
"""
        
        try:
            # Call LLM via inherited ChatAgent
            response = await self.run(prompt)
            
            # Decode unicode safely to avoid encoding errors
            response_text = decode_unicode_safely(response.text)
            
            # Parse JSON response (handle markdown code blocks)
            # Remove markdown code blocks if present
            text = response_text
            if text.startswith("```"):
                text = re.sub(r"^```(?:json)?\n?", "", text)  # Remove opening block
                text = re.sub(r"\n?```$", "", text)  # Remove closing block
            
            result = json.loads(text)
            rfq_logger.info(
                f"Compliance evaluation for {vendor.vendor_name}",
                workflow_id=workflow_id,
                recommendation=result.get("recommendation"),
            )
            return result
        except Exception as e:
            rfq_logger.error(
                f"Compliance evaluation failed for {vendor.vendor_name}: {type(e).__name__}: {str(e)[:100]}",
                workflow_id=workflow_id,
            )
            return {
                "vendor_id": vendor.vendor_id,
                "recommendation": "FLAG_CONCERN",
                "reasoning": "Could not parse compliance assessment",
                "risk_level": "HIGH",
                "confidence": 0.5,
            }


class FinancialAnalysisEvaluator(DemoBaseAgent):
    """
    Track 3: Cost anomaly detection & negotiation strategy using LLM.
    
    Rule-based approach can detect absolute prices, but LLM finds PATTERNS:
    - This vendor's price is 40% lower than others - why?
    - Volume discounts make sense, but 50% off seems suspicious
    - What's the negotiation strategy with this vendor?
    - Should we push back on price or accept delivery trade-off?
    
    System Prompt Strategy:
    - Provide all quotes for comparison
    - Give vendor profiles
    - Ask LLM to identify anomalies + strategy
    - Return structured decision with negotiation tactics
    """
    
    SYSTEM_PROMPT = """
You are a specialized financial analyst for RFQ evaluation.

Your role: Analyze vendor quotes, detect anomalies, and recommend negotiation strategy.

You are given:
1. Multiple vendor quotes for the same product/quantity
2. Vendor profiles (ratings, lead times, history)
3. Your company's budget/targets

Your task:
- Identify price anomalies (suspiciously high/low)
- Understand price variance (volume discount, quality trade-off, risk?)
- Recommend negotiation approach: ACCEPT / NEGOTIATE / REJECT
- Suggest negotiation talking points

Output format:
```json
{
    "price_analysis": "summary of pricing patterns",
    "anomalies": ["anomaly1", "anomaly2"],
    "best_value_vendor": "V001",
    "negotiation_strategy": {
        "vendor_id": "V002",
        "approach": "NEGOTIATE|ACCEPT|REJECT",
        "talking_points": ["point1", "point2"],
        "target_price": 1500.00,
        "trade_off_offer": "5 day faster delivery in exchange for price increase"
    },
    "recommendation": "V001 best value, but consider negotiating with V002",
    "confidence": 0.88
}
```
"""
    
    def __init__(self, product_name: str, quantity: int):
        """
        Initialize financial evaluator.
        
        Args:
            product_name: Product being evaluated
            quantity: Order quantity for context
        """
        self.product_name = product_name
        self.quantity = quantity
        
        super().__init__(
            name="Financial Analysis Evaluator",
            instructions=self.SYSTEM_PROMPT,
            model="gpt-4o",
            temperature=0.4,  # Slightly higher for strategy creativity
        )
        
        logger.info(f"FinancialAnalysisEvaluator initialized for {product_name}x{quantity}")
    
    async def analyze_quotes(
        self,
        vendors: List[VendorProfile],
        quotes: List[QuoteResponse],
        workflow_id: str,
    ) -> Dict[str, Any]:
        """
        Analyze quotes and recommend negotiation strategy.
        
        Args:
            vendors: List of vendors
            quotes: List of price quotes
            workflow_id: Workflow ID for tracing
            
        Returns:
            Analysis with anomalies, best value, negotiation strategy
        """
        # Format quote data for LLM
        quote_summary = "\n".join([
            f"  {v.vendor_name}: ${q.total_price:.2f} ({q.unit_price:.2f} per unit, "
            f"{q.delivery_lead_days} day lead)"
            for v, q in zip(vendors, quotes)
        ])
        
        prompt = f"""
ANALYZE THESE QUOTES FOR {self.product_name}:

Quantity: {self.quantity} units

{quote_summary}

What patterns do you see? Any suspicious prices?
Which offers the best value? How should we negotiate?
"""
        
        try:
            response = await self.run(prompt)
            
            # Decode unicode safely to avoid encoding errors
            response_text = decode_unicode_safely(response.text)
            
            # Remove markdown code blocks if present
            text = response_text
            if text.startswith("```"):
                text = re.sub(r"^```(?:json)?\n?", "", text)
                text = re.sub(r"\n?```$", "", text)
            
            result = json.loads(text)
            rfq_logger.info(
                f"Financial analysis for {self.product_name}",
                workflow_id=workflow_id,
                best_value=result.get("best_value_vendor"),
            )
            return result
        except Exception as e:
            rfq_logger.error(
                f"Financial analysis failed: {type(e).__name__}: {str(e)[:100]}",
                workflow_id=workflow_id,
            )
            return {
                "price_analysis": "Error during analysis",
                "recommendation": "Manual review needed",
                "confidence": 0.5,
            }


class DeliveryRiskAssessor(DemoBaseAgent):
    """
    Track 2: Delivery risk assessment (mostly rule-based, LLM for nuance).
    
    Rule-based: Check lead times, capacity, geography
    LLM-enhanced: Flag geopolitical/supply chain risks
    
    - Vendor in high-risk region? What's the supply chain risk?
    - Lead time seems long for this vendor - is there a reason?
    - Multiple vendors in same region - concentration risk?
    
    This one is lighter on LLM since delivery is mostly deterministic.
    """
    
    SYSTEM_PROMPT = """
You are a supply chain risk analyst for RFQ evaluation.

Your role: Assess geopolitical, supply chain, and delivery risks.

Consider:
1. Vendor location and geopolitical factors
2. Lead time vs. required delivery date
3. Vendor concentration risk (multiple orders from same region)
4. Capacity risk (can vendor handle this volume?)

Flag any red flags that impact delivery reliability.

Output format:
```json
{
    "geopolitical_risk": "LOW|MEDIUM|HIGH",
    "supply_chain_risk": "LOW|MEDIUM|HIGH",
    "capacity_concern": boolean,
    "lead_time_status": "COMFORTABLE|TIGHT|RISKY",
    "red_flags": ["flag1"],
    "recommendation": "APPROVE|MONITOR|REJECT",
    "reasoning": "explanation"
}
```
"""
    
    def __init__(self, requirements: ProductRequirements):
        """Initialize delivery risk assessor."""
        self.requirements = requirements
        
        super().__init__(
            name="Delivery Risk Assessor",
            instructions=self.SYSTEM_PROMPT,
            model="gpt-4o",
            temperature=0.3,
        )
    
    async def assess_delivery_risk(
        self,
        vendor: VendorProfile,
        workflow_id: str,
    ) -> Dict[str, Any]:
        """Assess delivery risk for a vendor."""
        distance = getattr(vendor, 'distance_miles', 0)
        
        # Calculate delivery confidence based on distance and lead time
        # Closer = higher confidence, further = lower confidence
        distance_factor = max(0.2, 1.0 - (distance / 10000))  # 0-5600 miles mapped to 0.44-1.0
        lead_time_buffer = self.requirements.max_lead_time_days - vendor.estimated_lead_time_days
        lead_time_factor = max(0.1, 1.0 if lead_time_buffer > 14 else 0.5)  # 0.5-1.0 based on buffer
        
        base_confidence = (distance_factor * 0.6 + lead_time_factor * 0.4)  # 60% distance, 40% lead time
        
        prompt = f"""
ASSESS DELIVERY RISK FOR:

Vendor: {vendor.vendor_name}
Country: {vendor.country}
Distance: {distance} miles
Lead Time: {vendor.estimated_lead_time_days} days
Required Delivery: {self.requirements.desired_delivery_date}
Max Lead Time Allowed: {self.requirements.max_lead_time_days} days
Capacity: {getattr(vendor, 'capacity_units_per_month', 'Unknown')} units/month
Required: {self.requirements.quantity} units

Based on distance ({distance} miles) and lead time ({vendor.estimated_lead_time_days} days), assess delivery feasibility.
Factors to consider: shipping time, customs clearance for international orders, buffer time.

Base confidence from logistics: {base_confidence:.2f}
Consider: Do they have enough capacity? Will they meet the deadline?
"""
        
        try:
            response = await self.run(prompt)
            
            # Decode unicode safely to avoid encoding errors
            response_text = decode_unicode_safely(response.text)
            
            # Remove markdown code blocks if present
            text = response_text
            if text.startswith("```"):
                text = re.sub(r"^```(?:json)?\n?", "", text)
                text = re.sub(r"\n?```$", "", text)
            
            result = json.loads(text)
            return result
        except Exception as e:
            rfq_logger.error(
                f"Delivery assessment failed for {vendor.vendor_name}: {type(e).__name__}: {str(e)[:100]}",
                workflow_id=workflow_id,
            )
            return {"recommendation": "MONITOR", "reasoning": "Error during delivery assessment", "confidence": 0.5}


# ============================================================================
# Factory Extensions for LLM-Enhanced Agents
# ============================================================================

class LLMEvaluationAgentFactory:
    """
    Factory for creating LLM-enhanced evaluation agents.
    
    Follows pattern from src.agents.factory.AgentFactory
    but creates specialized evaluation agents instead of general-purpose agents.
    """
    
    @staticmethod
    def create_compliance_evaluator(
        requirements: ProductRequirements,
    ) -> CertificationComplianceEvaluator:
        """Create compliance evaluator with LLM."""
        return CertificationComplianceEvaluator(requirements)
    
    @staticmethod
    def create_financial_evaluator(
        product_name: str,
        quantity: int,
    ) -> FinancialAnalysisEvaluator:
        """Create financial evaluator with LLM."""
        return FinancialAnalysisEvaluator(product_name, quantity)
    
    @staticmethod
    def create_delivery_assessor(
        requirements: ProductRequirements,
    ) -> DeliveryRiskAssessor:
        """Create delivery assessor with LLM."""
        return DeliveryRiskAssessor(requirements)
